from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
from sentence_transformers import SentenceTransformer, util
import torch
import joblib
import os

# =====================
# 1. Load model + dataset
# =====================
print("🔄 Đang load model SBERT...")
model = SentenceTransformer("keepitreal/vietnamese-sbert")

print("📂 Đang load dataset...")
df = pd.read_csv("merged_data.csv")
df.dropna(inplace=True)

corpus = df["ingredients"].astype(str).tolist()
embedding_file = "embeddings.pkl"

# =====================
# 2. Load hoặc tạo embeddings
# =====================
if os.path.exists(embedding_file):
    print("📦 Đang load embeddings từ file...")
    corpus_embeddings = joblib.load(embedding_file)
else:
    print("⚡ Tạo embeddings mới cho dataset...")
    corpus_embeddings = model.encode(corpus, convert_to_tensor=True)
    joblib.dump(corpus_embeddings, embedding_file)
    print(f"✅ Đã lưu embeddings vào {embedding_file}")

print("🚀 API sẵn sàng!")

# =====================
# 3. Khởi tạo API
# =====================
app = FastAPI(
    title="Food Recommendation API",
    description="API gợi ý món ăn từ nguyên liệu (SBERT + FastAPI)",
    version="1.1"
)

# Request body
class RecommendRequest(BaseModel):
    ingredients: str
    top_k: int = 5

# =====================
# 4. Endpoint API
# =====================
@app.post("/recommend")
def recommend_food(req: RecommendRequest):
    query_embedding = model.encode(req.ingredients, convert_to_tensor=True)

    hits = util.semantic_search(query_embedding, corpus_embeddings, top_k=req.top_k)[0]

    results = []
    for hit in hits:
        idx = hit["corpus_id"]

        # Lấy toàn bộ row dưới dạng dict
        row_data = df.iloc[idx].to_dict()
        row_data["similarity"] = round(float(hit["score"]), 3)

        results.append(row_data)

    return {
        "query": req.ingredients,
        "recommendations": results
    }

# =====================
# 5. Run server
# =====================
# Chạy bằng:
# uvicorn app:app --reload
