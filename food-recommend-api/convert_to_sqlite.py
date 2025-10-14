import pandas as pd
import sqlite3
from pathlib import Path

# File nguồn và đích
DATA_PATH = Path(__file__).resolve().parent / "merged_data.csv"
DB_PATH = Path(__file__).resolve().parent / "food_data.db"

def csv_to_sqlite():
    print("🔄 Đang đọc CSV...")
    df = pd.read_csv(DATA_PATH)

    # Làm sạch dữ liệu cơ bản
    df = df.fillna("")

    print("💾 Đang ghi vào SQLite...")
    conn = sqlite3.connect(DB_PATH)

    # Ghi vào bảng 'foods'
    df.to_sql("foods", conn, if_exists="replace", index=False)

    # Tạo index giúp tăng tốc query
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_id ON foods(id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_views ON foods(views DESC)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_category ON foods(category)")
    conn.commit()
    conn.close()

    print(f"✅ Đã lưu vào {DB_PATH} ({len(df)} dòng)")

if __name__ == "__main__":
    csv_to_sqlite()
