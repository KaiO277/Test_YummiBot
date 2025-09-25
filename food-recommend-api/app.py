from fastapi import FastAPI, Query
from pydantic import BaseModel
import pandas as pd
from sentence_transformers import SentenceTransformer, util
import torch
import re

# ============================
# 1. Khởi tạo app
# ============================
app = FastAPI(title="Food Recommendation API")

# ============================
# 2. Load dataset & SBERT model (chỉ load 1 lần khi start)
# ============================
df = pd.read_csv("merged_data.csv")  # cột: ten_mon, ingredients, link, ...
df = df.dropna(subset=["ingredients", "ten_mon"])

model = SentenceTransformer("keepitreal/vietnamese-sbert")

# Load embeddings đã lưu hoặc encode mới
try:
    corpus_embeddings = torch.load("food_embeddings.pt")
    print("✅ Loaded embeddings từ file food_embeddings.pt")
except:
    print("⚠️ Không tìm thấy embeddings, tiến hành encode...")
    corpus = (df["ten_mon"] + " " + df["ingredients"]).tolist()
    corpus_embeddings = model.encode(corpus, convert_to_tensor=True, show_progress_bar=True)
    torch.save(corpus_embeddings, "food_embeddings.pt")
    print("✅ Đã lưu embeddings vào food_embeddings.pt")

# ============================
# 3. Hàm keyword overlap
# ============================
def keyword_overlap(query: str, text: str) -> float:
    query_tokens = set(re.findall(r"\w+", query.lower()))
    text_tokens = set(re.findall(r"\w+", text.lower()))
    if not query_tokens:
        return 0.0
    return len(query_tokens & text_tokens) / len(query_tokens)

# ============================
# 4. Hàm recommend
# ============================
def recommend_food(query: str, top_k: int = 5, alpha: float = 0.7):
    query_embedding = model.encode(query, convert_to_tensor=True)

    # SBERT similarity
    cos_scores = util.cos_sim(query_embedding, corpus_embeddings)[0]
    top_results = torch.topk(cos_scores, k=top_k * 3)

    results = []
    for score, idx in zip(top_results[0], top_results[1]):
        row = df.iloc[idx.item()]
        text = f"{row['ten_mon']} {row['ingredients']}"

        kw_score = keyword_overlap(query, text)
        final_score = alpha * float(score) + (1 - alpha) * kw_score

        results.append({
            "ten_mon": row["ten_mon"],
            "ingredients": row["ingredients"],
            "link": row.get("link", ""),
            "similarity": float(score),
            "keyword_score": kw_score,
            "final_score": final_score
        })

    results = sorted(results, key=lambda x: x["final_score"], reverse=True)[:top_k]
    return results

# ============================
# 5. API Endpoints
# ============================

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5
    alpha: float = 0.7

@app.post("/recommend")
def recommend(req: QueryRequest):
    results = recommend_food(req.query, top_k=req.top_k, alpha=req.alpha)
    return {"query": req.query, "results": results}

@app.get("/")
def root():
    return {"message": "Food Recommendation API is running 🚀"}
