import os
import json
import re
import asyncio # ✅ PHẢI CÓ DÒNG NÀY ĐỂ GIẢI QUYẾT LỖI 'await'
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError as APIError 

# --- Cấu hình Ban đầu ---
dotenv_path = find_dotenv()
print("Đường dẫn .env:", dotenv_path)
load_dotenv(dotenv_path=dotenv_path)

# Cấu hình Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
print("GOOGLE_API_KEY:", os.getenv("GOOGLE_API_KEY"))

router = APIRouter()

# --- Định nghĩa Dữ liệu ---

class NutritionRequest(BaseModel):
    ingredients: str

DV_VALUES = {
    "calories": 2000,
    "total_fat": 78,    # g
    "saturated_fat": 20, # g
    "total_carbohydrate": 275, # g
    "fiber": 28,        # g
    "protein": 50,      # g
    "calcium": 1300,    # mg
    "iron": 18,         # mg
    "sodium": 2300      # mg
}

# --- Hàm Hỗ trợ ---

def split_ingredients(ingredients: str, max_len: int = 500) -> list[str]:
    """Chia chuỗi nguyên liệu thành các đoạn nhỏ để gửi tới API."""
    words = ingredients.split(", ")
    chunks = []
    current_chunk = []
    current_length = 0

    for word in words:
        if current_length + len(word) + 2 > max_len:
            chunks.append(", ".join(current_chunk))
            current_chunk = [word]
            current_length = len(word)
        else:
            current_chunk.append(word)
            current_length += len(word) + 2

    if current_chunk:
        chunks.append(", ".join(current_chunk))

    return chunks

def parse_nutrition_data(raw_text: str) -> dict:
    """Xử lý phản hồi raw từ Gemini để trích xuất dữ liệu JSON, sử dụng regex."""
    # Tìm kiếm khối JSON thực tế ({...})
    match = re.search(r"(\{.*\})", raw_text, re.DOTALL)
    
    if match:
        clean_text = match.group(1).strip()
        # Loại bỏ các ký tự Markdown
        clean_text = clean_text.replace("```json", "").replace("```", "").strip()
    else:
        # Fallback làm sạch cơ bản
        clean_text = raw_text.strip().replace("```json", "").replace("```", "")
    
    try:
        return json.loads(clean_text)
    except json.JSONDecodeError as e:
        print(f"LỖI DEBUG JSON: JSONDecodeError: {e}")
        print(f"PHẢN HỒI THÔ: {raw_text}")
        raise HTTPException(
            status_code=500,
            detail="Gemini API không trả về định dạng JSON hợp lệ."
        )

# --- Endpoint Chính ---

@router.post("/nutrition")
async def get_nutrition(payload: NutritionRequest):
    """Endpoint phân tích dinh dưỡng của nguyên liệu sử dụng Gemini API."""
    chunks = split_ingredients(payload.ingredients)
    total_nutrition = {}
    
    # Sử dụng mô hình mới, ổn định
    model = genai.GenerativeModel('gemini-2.5-flash') 

    for chunk in chunks:
        prompt = f"""
        Phân tích dinh dưỡng của các nguyên liệu sau và trả về kết quả dưới dạng JSON. 
        Mỗi thành phần dinh dưỡng phải có đơn vị. Dữ liệu phải là tổng hợp của tất cả các nguyên liệu.
        Nguyên liệu: {chunk}
        
        Ví dụ định dạng JSON (CẦN ĐÚNG KHÓA VÀ ĐƠN VỊ):
        {{
            "calories": "250 kcal",
            "total_fat": "10 g",
            "saturated_fat": "2 g",
            "total_carbohydrate": "30 g",
            "fiber": "5 g",
            "protein": "15 g",
            "calcium": "150 mg",
            "iron": "2 mg",
            "sodium": "300 mg"
        }}
        
        TRẢ LỜI CHỈ BẰNG JSON, KHÔNG THÊM BẤT KỲ VĂN BẢN, GIẢI THÍCH NÀO KHÁC.
        """
        try:
            # ✅ SỬA LỖI: Bọc cuộc gọi đồng bộ bằng asyncio.to_thread()
            # Điều này cho phép chúng ta 'await' một hàm đồng bộ mà không chặn Event Loop.
            response = await asyncio.to_thread(model.generate_content, prompt)
            
            # Kiểm tra phản hồi rỗng
            if not response.text:
                 raise APIError(f"API không trả về nội dung hợp lệ (response.text rỗng) cho chunk: {chunk}")
                 
            nutrition_data = parse_nutrition_data(response.text)
            
            # Cộng dồn giá trị dinh dưỡng
            for key, value_str in nutrition_data.items():
                match = re.search(r"(\d+(\.\d+)?)\s*(kcal|g|mg)?", value_str)
                if match:
                    num = float(match.group(1))
                    unit = match.group(3) if match.group(3) else ""
                    
                    # Chuẩn hóa đơn vị: Chuyển mg sang g (trừ Calcium và Sodium)
                    if unit == "mg" and key not in ["calcium", "sodium"]:
                        num /= 1000
                        
                    total_nutrition[key] = total_nutrition.get(key, 0) + num
                    
        except HTTPException as e:
            raise e
        except APIError as e:
            print(f"LỖI DEBUG API: GoogleAPIError xảy ra: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Lỗi API Gemini: {e}. Vui lòng kiểm tra API Key và hạn mức sử dụng."
            )
        except Exception as e:
            print(f"LỖI DEBUG KHÔNG XÁC ĐỊNH: Exception xảy ra: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Có lỗi xảy ra không xác định trong quá trình xử lý: {e}"
            )

    # Tính toán phần trăm giá trị dinh dưỡng hàng ngày (Daily Value).
    daily_values_percent = {}
    for key, value in total_nutrition.items():
        if key in DV_VALUES:
            daily_values_percent[key] = round((value / DV_VALUES[key]) * 100, 2)
    
    return {
        "nutrition_values": total_nutrition,
        "daily_values_percent": daily_values_percent
    }