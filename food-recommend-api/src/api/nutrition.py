import os
import google.generativeai as genai
from google.generativeai.types import AsyncGenerateContentResponse
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import re
from dotenv import load_dotenv, find_dotenv
from pathlib import Path

dotenv_path = find_dotenv()
print("Đường dẫn .env:", dotenv_path)
load_dotenv(dotenv_path=dotenv_path)

# ✅ Cấu hình Gemini với API key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
print("GOOGLE_API_KEY:", os.getenv("GOOGLE_API_KEY"))

router = APIRouter()

class NutritionRequest(BaseModel):
    ingredients: str

DV_VALUES = {
    "calories": 2000,
    "total_fat": 78,
    "saturated_fat": 20,
    "total_carbohydrate": 275,
    "fiber": 28,
    "protein": 50,
    "calcium": 1300,
    "iron": 18,
    "sodium": 2300
}

def split_ingredients(ingredients: str, max_len: int = 500) -> list[str]:
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
    # 1. Tìm kiếm khối JSON thực tế (từ { đầu tiên đến } cuối cùng)
    # re.DOTALL cho phép . khớp với cả ký tự xuống dòng
    match = re.search(r"(\{.*\})", raw_text, re.DOTALL)
    
    if match:
        clean_text = match.group(1)
        # Loại bỏ các ký tự Markdown nếu chúng vẫn còn dính vào khối JSON (ví dụ: ```json)
        clean_text = clean_text.replace("```json", "").replace("```", "").strip()
    else:
        # 2. Nếu không tìm thấy khối JSON rõ ràng, thực hiện làm sạch cơ bản
        clean_text = raw_text.strip().replace("```json", "").replace("```", "")
    
    try:
        return json.loads(clean_text)
    except json.JSONDecodeError as e:
        print(f"Lỗi JSONDecodeError: {e}")
        print(f"Phản hồi thô từ Gemini: {raw_text}")
        raise HTTPException(
            status_code=500,
            detail="Có lỗi xảy ra khi parse JSON từ phản hồi của Gemini. Hãy kiểm tra console để xem phản hồi thô."
        )
@router.post("/nutrition")
async def get_nutrition(payload: NutritionRequest):
    chunks = split_ingredients(payload.ingredients)
    total_nutrition = {}
    model = genai.GenerativeModel('gemini-pro')

    for chunk in chunks:
        prompt = f"""
        Phân tích dinh dưỡng của các nguyên liệu sau và trả về kết quả dưới dạng JSON. 
        Mỗi thành phần dinh dưỡng phải có đơn vị.
        Nguyên liệu: {chunk}
        Ví dụ định dạng JSON:
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
            # Sử dụng phương thức đồng bộ, KHÔNG dùng await
            response = model.generate_content(prompt)
            nutrition_data = parse_nutrition_data(response.text)
            for key, value_str in nutrition_data.items():
                match = re.search(r"(\d+(\.\d+)?)\s*(kcal|g|mg)?", value_str)
                if match:
                    num = float(match.group(1))
                    unit = match.group(3) if match.group(3) else ""
                    if unit == "mg" and key != "calcium":
                        num /= 1000
                    total_nutrition[key] = total_nutrition.get(key, 0) + num
        except HTTPException as e:
            raise e
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Có lỗi xảy ra khi gọi API Gemini: {e}"
            )

    daily_values_percent = {}
    for key, value in total_nutrition.items():
        if key in DV_VALUES:
            daily_values_percent[key] = round((value / DV_VALUES[key]) * 100, 2)
    return {
        "nutrition_values": total_nutrition,
        "daily_values_percent": daily_values_percent
    }