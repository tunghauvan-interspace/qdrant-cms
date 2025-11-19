import os
import json
import google.generativeai as genai
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure the API key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# --- 1. Định nghĩa Cấu trúc Dữ liệu Chung (Generic Schema) ---
# Mục tiêu: Trích xuất các điểm chính và tóm tắt tổng thể của tài liệu.

class KeyPoint(BaseModel):
    """Cấu trúc cho một điểm chính/ý chính của tài liệu."""
    point: str = Field(description="Một điểm/ý chính quan trọng được trích xuất từ tài liệu.")

class DocumentSummary(BaseModel):
    """Cấu trúc chung cho bản tóm tắt của bất kỳ tài liệu nào."""
    document_title: str = Field(description="Tiêu đề chính của tài liệu.")
    summary: str = Field(description="Bản tóm tắt chi tiết, 3-4 câu về nội dung tài liệu.")
    key_points: list[KeyPoint] = Field(description="Danh sách 5-7 điểm chính hoặc kết luận quan trọng của tài liệu.")


def parse_generic_pdf(pdf_path: str):
    """
    Phân tích một tệp PDF chung và trích xuất dữ liệu có cấu trúc.
    """
    try:
        # Khởi tạo Model
        model = genai.GenerativeModel('gemini-2.5-flash')
    except Exception as e:
        print("Lỗi: Không tìm thấy GOOGLE_API_KEY. Vui lòng đặt biến môi trường.")
        return

    uploaded_file = None
    try:
        print(f"Bắt đầu tải tệp: {pdf_path}")
        
        # --- 2. Tải tệp PDF lên API ---
        uploaded_file = genai.upload_file(pdf_path)
        print(f"Đã tải lên tệp: {uploaded_file.name}")

        # Chuẩn bị cấu hình cho Structured Output (JSON Schema)
        response_schema = {
            "type": "object",
            "properties": {
                "document_title": {
                    "type": "string",
                    "description": "Tiêu đề chính xác của tài liệu."
                },
                "full_markdown_text": {
                    "type": "string",
                    "description": "Toàn bộ nội dung văn bản của tài liệu được chuyển đổi sang định dạng Markdown. Giữ nguyên cấu trúc, tiêu đề, danh sách và nội dung chi tiết. Không tóm tắt."
                }
            },
            "required": ["document_title", "full_markdown_text"]
        }
        generation_config = genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=response_schema,
            temperature=0.1, # Giảm temperature để tăng tính chính xác
        )

        prompt_text = (
            "Bạn là một chuyên gia chuyển đổi tài liệu (OCR và Layout Analysis). "
            "Nhiệm vụ của bạn là chuyển đổi toàn bộ nội dung tệp PDF sang định dạng Markdown. "
            "Yêu cầu:\n"
            "1. **Toàn vẹn nội dung**: Giữ nguyên toàn bộ nội dung văn bản, KHÔNG được tóm tắt, KHÔNG lược bỏ bất kỳ chi tiết nào.\n"
            "2. **Cấu trúc**: Bảo toàn cấu trúc phân cấp (Tiêu đề #, ##, ###), danh sách (- hoặc 1.), và định dạng văn bản.\n"
            "3. **Định dạng**: Trả về kết quả dưới dạng JSON với trường 'full_markdown_text' chứa nội dung Markdown đầy đủ."
        )
        
        # --- 3. Gọi API với Tệp và Cấu hình ---
        response = model.generate_content(
            [prompt_text, uploaded_file],
            generation_config=generation_config,
        )

        print("\n--- KẾT QUẢ PHÂN TÍCH (Structured JSON) ---")
        # Phân tích chuỗi JSON trả về
        structured_data = json.loads(response.text)
        # print(json.dumps(structured_data, indent=4, ensure_ascii=False)) # Không in JSON quá dài

        # In ra dưới dạng Markdown dễ đọc hơn
        print("\n--- KẾT QUẢ DƯỚI DẠNG VĂN BẢN DỄ ĐỌC ---")
        print(f"## 📝 {structured_data.get('document_title', 'Tài Liệu')}")
        print("---")
        full_text = structured_data.get('full_markdown_text', '')
        print(full_text[:500] + "...\n\n(Nội dung quá dài, đã cắt bớt khi hiển thị trên terminal)")
        
        # Lưu vào file
        output_file = "extracted_full_text.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"# {structured_data.get('document_title')}\n\n")
            f.write(full_text)
        print(f"\n✅ Đã lưu toàn bộ nội dung vào file: {output_file}")


    except Exception as e:
        print(f"\nĐã xảy ra lỗi trong quá trình trích xuất: {e}")

    finally:
        # --- 4. Làm sạch: Xóa tệp đã tải lên ---
        if uploaded_file:
            print(f"\nĐang xóa tệp {uploaded_file.name} khỏi dịch vụ...")
            genai.delete_file(uploaded_file.name)
            print("Đã xóa thành công.")

if __name__ == "__main__":
    # Thay thế bằng đường dẫn thực tế đến Tệp PDF chung của bạn
    PDF_FILE_PATH = "example.pdf"
    
    if os.path.exists(PDF_FILE_PATH):
        parse_generic_pdf(PDF_FILE_PATH)
    else:
        print(f"Lỗi: Không tìm thấy tệp {PDF_FILE_PATH}. Vui lòng thay đổi đường dẫn.")