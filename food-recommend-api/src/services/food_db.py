import sqlite3
from pathlib import Path
import pandas as pd
import os

BASE_DIR = Path(__file__).resolve().parents[3]  # Thư mục gốc dự án
DB_PATH = BASE_DIR / "food-recommend-api\\food_data.db"

def get_all_categories():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT id, category_name, category_image_local FROM categories", conn)
    conn.close()

    # ✅ Chuyển local path sang đường dẫn /static/
    df["category_image_url"] = df["category_image_local"].apply(
        lambda x: f"/static/{os.path.basename(x)}" if x else None
    )

    return df.to_dict(orient="records")

def get_top_foods(limit: int = 6, category: str | None = None):
    conn = sqlite3.connect(DB_PATH)

    if category:
        query = """
            SELECT id, ten_mon, anh, mo_ta, category, views, link
            FROM foods
            WHERE category = ?
            ORDER BY views DESC
            LIMIT ?
        """
        df = pd.read_sql_query(query, conn, params=(category, limit))
    else:
        query = """
            SELECT id, ten_mon, anh, mo_ta, category, views, link
            FROM foods
            ORDER BY views DESC
            LIMIT ?
        """
        df = pd.read_sql_query(query, conn, params=(limit,))

    conn.close()
    return df.to_dict(orient="records")


def get_food_detail(food_id: int):
    """Lấy chi tiết 1 món ăn theo ID"""
    conn = sqlite3.connect(DB_PATH)
    query = """
        SELECT id, ten_mon, anh, mo_ta, ingredients, ready_html, step_html, category, views, link
        FROM foods
        WHERE id = ?
    """
    df = pd.read_sql_query(query, conn, params=(food_id,))
    conn.close()

    if df.empty:
        return None
    return df.to_dict(orient="records")[0]
