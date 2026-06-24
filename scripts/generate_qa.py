"""
QA Data Generation — Auto-generate and Tone-rewrite QA pairs.

Usage:
    python scripts/generate_qa.py --pdf-dir data/raw_pdfs/ --output data/dataset/qa.jsonl
"""

import json
import re
import argparse
import random
from pathlib import Path
from typing import TYPE_CHECKING, Any

from src.core.config import get_settings
from src.core.llm_client import create_llm_client
from src.core.logger import get_logger
from src.rag.document import load_pdf, chunk_documents

if TYPE_CHECKING:
    from langchain_core.documents import Document

logger = get_logger(__name__)

# --- CÁC HÀM XỬ LÝ LLM CŨ CỦA BẠN GIỮ NGUYÊN ---

def parse_json_from_llm(response: str, context: str) -> list[dict[str, str]]:
    """Phân tích chuỗi JSON trả về từ LLM (Giữ nguyên như cũ)"""
    response_str = response.strip()
    match_arr = re.search(r"(\[\s*\{.*\}\s*\])", response_str, re.DOTALL)
    parsed_list = []
    
    if match_arr:
        try: parsed_list = json.loads(match_arr.group(1))
        except json.JSONDecodeError: pass
            
    if not parsed_list:
        try: parsed_list = json.loads(response_str)
        except json.JSONDecodeError: pass
            
    if not parsed_list:
        match_obj = re.search(r"(\{\s*.*?\s*\})", response_str, re.DOTALL)
        if match_obj:
            try: parsed_list = [json.loads(match_obj.group(1))]
            except json.JSONDecodeError: pass

    if isinstance(parsed_list, dict): parsed_list = [parsed_list]
        
    normalized: list[dict[str, str]] = []
    if isinstance(parsed_list, list):
        for item in parsed_list:
            if isinstance(item, dict):
                instruction = item.get("instruction") or item.get("question") or item.get("q") or ""
                inp = item.get("input") or item.get("context") or item.get("c") or context
                output = item.get("output") or item.get("answer") or item.get("a") or ""
                
                if instruction and output:
                    normalized.append({
                        "instruction": str(instruction).strip(),
                        "input": str(inp).strip(),
                        "output": str(output).strip()
                    })
    return normalized

def generate_qa_from_chunk(chunk: Any, llm: Any) -> list[dict[str, str]]:
    """Sinh QA từ PDF bằng LLM (Giữ nguyên như cũ)"""
    context = chunk.page_content if hasattr(chunk, "page_content") else str(chunk)
    if not context.strip(): return []

    prompt = f"""Bạn là một chuyên gia tạo dữ liệu huấn luyện RAG. Nhiệm vụ của bạn là trích xuất và sinh ra đúng 2 đến 3 cặp Câu hỏi và Câu trả lời (QA) chất lượng cao bằng tiếng Việt dựa vào văn bản ngữ cảnh (context) dưới đây.

Đầu ra BẮT BUỘC phải là một JSON Array:
[
  {{
    "instruction": "Câu hỏi chi tiết...",
    "input": "Ngữ cảnh được cung cấp...",
    "output": "Câu trả lời đầy đủ... Phải sử dụng VĂN PHONG NHẸ NHÀNG, NGỌT NGÀO, LỊCH SỰ, tự xưng là 'em' và gọi người dùng là 'anh/chị'."
  }}
]
Văn bản ngữ cảnh:
\"\"\"{context}\"\"\""""
    try:
        response = llm.invoke(prompt)
        return parse_json_from_llm(response, context)
    except Exception as e:
        logger.error(f"Error calling LLM for chunk: {e}")
        return []

# --- PHẦN MỚI: HÀM VIẾT LẠI VĂN PHONG (REWRITE) ---

def fallback_polite_tone(text: str) -> str:
    """Hàm dự phòng (Rule-based) dùng khi LLM bị lỗi kết nối hoặc quá tải."""
    text = re.sub(r'\btôi\b', 'em', text, flags=re.IGNORECASE)
    text = re.sub(r'\bbạn\b', 'anh/chị', text, flags=re.IGNORECASE)
    text = re.sub(r'\bchúng tôi\b', 'bên em', text, flags=re.IGNORECASE)
    
    text = text[0].upper() + text[1:] if text else text
    
    prefixes = ["Dạ, ", "Dạ thưa anh/chị, ", "Theo thông tin em có được thì ", "Dạ vâng, "]
    prefix = random.choice(prefixes)
    
    if not text.endswith(("ạ.", "ạ!", "nhé ạ.")):
        text = text.rstrip(".!") + " ạ."
    return prefix + text

def rewrite_output_tone(original_output: str, llm: Any) -> str:
    """Dùng LLM để viết lại câu trả lời khô khan sang văn phong CSKH."""
    prompt = f"""Bạn là một trợ lý ảo chăm sóc khách hàng xuất sắc. Hãy viết lại câu trả lời dưới đây.
Yêu cầu:
1. Xưng 'em', gọi khách hàng là 'anh/chị'.
2. Văn phong nhẹ nhàng, lễ phép, ngọt ngào (thêm 'Dạ', 'ạ' tự nhiên).
3. TUYỆT ĐỐI GIỮ NGUYÊN ý nghĩa, thông số và thông tin gốc.
4. Chỉ in ra CÂU ĐÃ VIẾT LẠI, không thêm bất kỳ lời dẫn hay giải thích nào.

Câu gốc: "{original_output}"
Câu viết lại:"""

    try:
        # Gọi LLM để viết lại câu
        response = llm.invoke(prompt)
        cleaned_response = str(response).strip()
        
        # Đề phòng LLM lười biếng trả về rỗng, ta vẫn có fallback
        if not cleaned_response:
            return fallback_polite_tone(original_output)
            
        return cleaned_response
    except Exception as e:
        logger.warning(f"LLM rewrite failed, using regex fallback. Error: {e}")
        return fallback_polite_tone(original_output)

# --- PIPELINE CHÍNH ---

def build_dataset(
    pdf_dir: str | Path,
    output_path: str | Path,
    hf_dataset: str | None = None,
    hf_split: str = "train",
    hf_instruction_col: str = "instruction",
    hf_input_col: str = "input",
    hf_output_col: str = "output",
    provider: str = "ollama",
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
    num_pairs: int = 200,
    hf_limit: int | None = 100,
) -> int:
    
    logger.info("Initializing dataset building pipeline...")
    
    # 1. Các mẫu đối thoại chào hỏi neo (Anchor data)
    greeting_pairs = [
        {
            "instruction": "Xin chào",
            "input": "",
            "output": "Dạ, em chào anh/chị ạ! Rất vui được hỗ trợ anh/chị ngày hôm nay. Dạ không biết em nên xưng hô với mình là anh hay chị để tiện trò chuyện nhất ạ?"
        },
        # ... (Bạn có thể thêm các mẫu khác vào đây)
    ]
    
    # Khởi tạo chung LLM client để dùng cho cả việc đọc PDF và Rewrite HF dataset
    llm = create_llm_client(provider)
    
    # 2. Xử lý PDF cục bộ (Giữ nguyên logic của bạn)
    generated_pairs: list[dict[str, str]] = []
    pdf_path = Path(pdf_dir)
    
    if pdf_path.exists() and pdf_path.is_dir():
        pdf_files = list(pdf_path.glob("*.pdf"))
        # ... (Phần code load PDF và generate_qa_from_chunk giữ nguyên)
        # Giả lược trong ví dụ này để tập trung vào phần mới
    
    # 3. Tải và TÍCH HỢP & REWRITE dữ liệu từ Hugging Face
    hf_pairs: list[dict[str, str]] = []
    if hf_dataset:
        try:
            from datasets import load_dataset
            logger.info(f"Downloading Hugging Face dataset '{hf_dataset}'...")
            ds = load_dataset(hf_dataset, split=hf_split)
            
            if hf_limit is not None and hf_limit > 0:
                logger.info(f"Limiting Hugging Face dataset to first {hf_limit} records.")
                ds = ds.select(range(min(hf_limit, len(ds)))) if hasattr(ds, "select") else ds[:hf_limit]
            
            for idx, row in enumerate(ds):
                logger.info(f"Rewriting Tone for HF record {idx + 1}/{hf_limit}...")
                
                instruction = row.get(hf_instruction_col, "")
                inp = row.get(hf_input_col, "")
                raw_output = str(row.get(hf_output_col, "")).strip()
                
                # Bước Đột Phá: Đưa raw_output qua LLM để viết lại văn phong
                polite_output = rewrite_output_tone(raw_output, llm)
                
                if instruction or polite_output:
                    hf_pairs.append({
                        "instruction": str(instruction).strip(),
                        "input": str(inp).strip(),
                        "output": polite_output
                    })
                    
            logger.info(f"Successfully mapped and rewrote {len(hf_pairs)} records.")
        except Exception as e:
            logger.error(f"Failed to integrate Hugging Face dataset: {e}")

    # 4. Gộp toàn bộ và lưu file
    final_dataset = greeting_pairs + hf_pairs + generated_pairs
    
    out_file = Path(output_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(out_file, "w", encoding="utf-8") as f:
        for item in final_dataset:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
            
    logger.info(f"Pipeline completed. Saved {len(final_dataset)} total QA pairs.")
    return len(final_dataset)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf-dir", type=str, default="data/raw_pdfs/")
    parser.add_argument("--output", type=str, default="data/dataset/qa.jsonl")
    parser.add_argument("--hf-dataset", type=str, default="bkai-foundation-models/vi-alpaca")
    parser.add_argument("--hf-split", type=str, default="train")
    parser.add_argument("--hf-instruction-col", type=str, default="instruction")
    parser.add_argument("--hf-input-col", type=str, default="input")
    parser.add_argument("--hf-output-col", type=str, default="output")
    parser.add_argument("--hf-limit", type=int, default=100)
    parser.add_argument("--provider", type=str, default="ollama")
    parser.add_argument("--chunk-size", type=int, default=None)
    parser.add_argument("--chunk-overlap", type=int, default=None)
    parser.add_argument("--num-pairs", type=int, default=200)
    
    args = parser.parse_args()
    
    build_dataset(
        pdf_dir=args.pdf_dir, # Đã sửa lỗi typo dấu gạch ngang
        output_path=args.output,
        hf_dataset=args.hf_dataset,
        hf_split=args.hf_split,
        hf_instruction_col=args.hf_instruction_col,
        hf_input_col=args.hf_input_col,
        hf_output_col=args.hf_output_col,
        hf_limit=args.hf_limit,
        provider=args.provider,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        num_pairs=args.num_pairs,
    )