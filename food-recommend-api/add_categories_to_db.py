import pandas as pd
import sqlite3
from pathlib import Path

# Đường dẫn file
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "food_data.db"
CATEGORY_PATH = BASE_DIR / "categories.csv"

def add_categories_to_db():
    if not CATEGORY_PATH.exists():
        print(f"❌ Không tìm thấy file {CATEGORY_PATH}")
        return
    
    df = pd.read_csv(CATEGORY_PATH)
    df = df.fillna("")

    # Đảm bảo có cột ID tự tăng (nếu chưa có)
    if "id" not in df.columns:
        df.insert(0, "id", range(1, len(df) + 1))

    print(f"📦 Đang thêm {len(df)} categories vào database...")

    conn = sqlite3.connect(DB_PATH)
    df.to_sql("categories", conn, if_exists="replace", index=False)

    # Tạo index giúp truy vấn nhanh
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_cat_id ON categories(id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cat_name ON categories(category_name)")
    conn.commit()
    conn.close()

    print(f"✅ Đã thêm bảng 'categories' ({len(df)} dòng) vào {DB_PATH}")

if __name__ == "__main__":
    add_categories_to_db()
