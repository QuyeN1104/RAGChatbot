import type { Conversation } from '../types';
const now = new Date().toISOString();
const msg = (id: string, role: 'user' | 'assistant', content: string) => ({ id, role, content, createdAt: now });
export const sampleConversations: Conversation[] = [
  { id: 'welcome-vietnam', title: 'Lên kế hoạch khám phá Việt Nam', group: 'Hôm nay', updatedAt: now, messages: [msg('m1', 'user', 'Gợi ý lịch trình 5 ngày khám phá miền Trung.'), msg('m2', 'assistant', 'Dưới đây là lịch trình cân bằng giữa **văn hoá, ẩm thực và nghỉ dưỡng**:\n\n| Ngày | Điểm đến | Trải nghiệm chính |\n| --- | --- | --- |\n| 1 | Đà Nẵng | Biển Mỹ Khê, bán đảo Sơn Trà |\n| 2 | Hội An | Phố cổ, lớp nấu ăn |\n| 3 | Huế | Đại Nội, ẩm thực cung đình |\n\n> Mẹo: Hãy dành một buổi tối đi bộ ở Hội An để tận hưởng không khí yên tĩnh.')] },
  { id: 'react-hooks', title: 'Hiểu rõ React Hooks', group: 'Hôm nay', updatedAt: now, messages: [msg('m3', 'user', 'Giải thích useMemo thật ngắn gọn.'), msg('m4', 'assistant', '`useMemo` ghi nhớ một giá trị đã tính và chỉ tính lại khi dependency thay đổi. Hãy dùng khi phép tính thực sự tốn kém.')] },
  { id: 'study-plan', title: 'Kế hoạch học TypeScript', group: '7 ngày trước', updatedAt: now, messages: [msg('m5', 'user', 'Lập kế hoạch học TypeScript trong 4 tuần.'), msg('m6', 'assistant', 'Bắt đầu với kiểu dữ liệu, chuyển sang generics, sau đó thực hành bằng một dự án React nhỏ.')] },
  { id: 'document-summary', title: 'Tóm tắt tài liệu sản phẩm', group: '7 ngày trước', updatedAt: now, messages: [msg('m7', 'user', 'Giúp tôi xây dựng khung tóm tắt PRD.'), msg('m8', 'assistant', 'Một bản tóm tắt PRD tốt nên có: vấn đề, đối tượng, mục tiêu, phạm vi, chỉ số thành công và rủi ro.')] },
  { id: 'python-api', title: 'Xây dựng REST API với Python', group: '30 ngày trước', updatedAt: now, messages: [msg('m9', 'user', 'Cho tôi ví dụ endpoint đơn giản.'), msg('m10', 'assistant', 'Ví dụ với FastAPI:\n\n```python\nfrom fastapi import FastAPI\n\napp = FastAPI()\n\n@app.get("/hello")\ndef hello():\n    return {"message": "Xin chào"}\n```')] },
];
export const suggestions = [
  { title: 'Giải thích một chủ đề khó', prompt: 'Hãy giải thích một chủ đề khó theo cách thật dễ hiểu', description: 'Biến khái niệm phức tạp thành ví dụ gần gũi' },
  { title: 'Viết và sửa mã nguồn', prompt: 'Giúp tôi viết và cải thiện một đoạn mã nguồn', description: 'Tạo mã sạch, tìm lỗi và đề xuất cải tiến' },
  { title: 'Lập kế hoạch học tập', prompt: 'Lập cho tôi một kế hoạch học tập thực tế', description: 'Xây lộ trình phù hợp với mục tiêu của bạn' },
  { title: 'Phân tích tài liệu', prompt: 'Phân tích và tóm tắt tài liệu này giúp tôi', description: 'Rút ra ý chính, dữ kiện và bước tiếp theo' },
];
export const models = ['Lumen 2.5', 'Lumen 2.5 Nhanh', 'Lumen 2.5 Suy luận'];
