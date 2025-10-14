# src/api/services/recommender.py
import pandas as pd
from pathlib import Path

# Tự động tìm đường dẫn đến merged_data.csv
BASE_DIR = Path(__file__).resolve().parents[3]  # Thư mục gốc dự án
DATA_PATH = BASE_DIR / "food-recommend-api\\merged_data.csv"

def get_top_foods(limit: int = 6):
    # Đọc CSV
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Không tìm thấy file CSV tại: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)

    # Kiểm tra cột 'views'
    if "views" not in df.columns:
        raise ValueError("File CSV không có cột 'views'.")

    # Sắp xếp giảm dần theo 'views'
    df = df.sort_values(by="views", ascending=False)

    # Lấy top món ăn
    top_foods = df.head(limit)

    # Chọn cột quan trọng để trả về
    result = top_foods[[
        "ten_mon", "anh", "mo_ta", "category", "views", "link"
    ]].to_dict(orient="records")

    return result
