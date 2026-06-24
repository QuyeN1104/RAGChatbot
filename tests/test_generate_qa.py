import json
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from langchain_core.documents import Document

from scripts.generate_qa import parse_json_from_llm, generate_qa_from_chunk, build_dataset


def test_parse_json_from_llm_valid_json():
    response = """
    [
        {"instruction": "What is RAG?", "input": "Retrieval Augmented Gen...", "output": "RAG is a technique..."}
    ]
    """
    context = "default context"
    res = parse_json_from_llm(response, context)
    assert len(res) == 1
    assert res[0]["instruction"] == "What is RAG?"
    assert res[0]["input"] == "Retrieval Augmented Gen..."
    assert res[0]["output"] == "RAG is a technique..."


def test_parse_json_from_llm_markdown_code_block():
    response = """
    Some introduction text...
    ```json
    [
        {
            "question": "What is RAG?",
            "context": "Context information",
            "answer": "Answer here"
        }
    ]
    ```
    Some outro text...
    """
    context = "default context"
    res = parse_json_from_llm(response, context)
    assert len(res) == 1
    assert res[0]["instruction"] == "What is RAG?"
    assert res[0]["input"] == "Context information"
    assert res[0]["output"] == "Answer here"


def test_parse_json_from_llm_single_dict_fallback():
    response = """
    {
        "q": "Single question?",
        "a": "Single answer."
    }
    """
    context = "default context"
    res = parse_json_from_llm(response, context)
    assert len(res) == 1
    assert res[0]["instruction"] == "Single question?"
    assert res[0]["input"] == context
    assert res[0]["output"] == "Single answer."


def test_parse_json_from_llm_invalid_format():
    response = "This is not json at all."
    res = parse_json_from_llm(response, "context")
    assert len(res) == 0


def test_generate_qa_from_chunk(mock_llm):
    # Mocking llm response to return valid JSON
    mock_llm.invoke = MagicMock(return_value="""
    [
        {"instruction": "Q1", "input": "C1", "output": "A1"},
        {"instruction": "Q2", "input": "C2", "output": "A2"}
    ]
    """)
    doc = Document(page_content="This is the page content of chunk.")
    res = generate_qa_from_chunk(doc, mock_llm)
    
    assert len(res) == 2
    assert res[0]["instruction"] == "Q1"
    assert res[1]["output"] == "A2"
    mock_llm.invoke.assert_called_once()


@patch("scripts.generate_qa.load_pdf")
@patch("scripts.generate_qa.chunk_documents")
@patch("scripts.generate_qa.create_llm_client")
@patch("datasets.load_dataset")
def test_build_dataset(
    mock_load_dataset,
    mock_create_llm,
    mock_chunk_docs,
    mock_load_pdf,
    tmp_path
):
    # Mock PDF loading
    mock_load_pdf.return_value = [Document(page_content="Page content")]
    
    # Mock chunking
    mock_chunk_docs.return_value = [
        Document(page_content="Chunk 1 content"),
        Document(page_content="Chunk 2 content")
    ]
    
    # Mock LLM Client
    mock_llm = MagicMock()
    mock_llm.invoke.side_effect = [
        '[{"instruction": "Q1", "input": "Chunk 1 content", "output": "A1"}]',
        '[{"instruction": "Q2", "input": "Chunk 2 content", "output": "A2"}]'
    ]
    mock_create_llm.return_value = mock_llm
    
    # Mock Hugging Face dataset load
    mock_hf_data = [
        {"instruction": "HF Q1", "input": "HF I1", "output": "HF A1"},
        {"instruction": "HF Q2", "input": "HF I2", "output": "HF A2"}
    ]
    mock_load_dataset.return_value = mock_hf_data
    
    # Setup directories
    pdf_dir = tmp_path / "pdfs"
    pdf_dir.mkdir()
    # Create a dummy PDF file name so it is found
    dummy_pdf = pdf_dir / "dummy.pdf"
    dummy_pdf.touch()
    
    output_file = tmp_path / "output.jsonl"
    
    # Run build_dataset
    total_saved = build_dataset(
        pdf_dir=pdf_dir,
        output_path=output_file,
        hf_dataset="dummy_hf",
        hf_split="train",
        provider="ollama",
        num_pairs=2
    )
    
    assert total_saved == 9 # 5 greetings + 2 HF + 2 generated
    assert output_file.exists()
    
    # Check JSONL contents
    with open(output_file, "r", encoding="utf-8") as f:
        lines = [json.loads(line) for line in f]
        
    assert len(lines) == 9
    # First elements are greeting templates
    assert lines[0]["instruction"] == "Xin chào"
    # Next elements should be HF dataset elements
    assert lines[5]["instruction"] == "HF Q1"
    # Last elements should be locally generated elements
    assert lines[7]["instruction"] == "Q1"
    assert lines[8]["instruction"] == "Q2"
