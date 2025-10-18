from fastapi import HTTPException
import pandas as pd
from sentence_transformers import SentenceTransformer, util
import torch
import re

class Recommender:
    def __init__(self):
        self.df = pd.read_csv("merged_data.csv")
        self.df = self.df.dropna(subset=["ingredients", "ten_mon"])
        
        # Nếu cột views không phải số, chuyển sang int
        self.df["views"] = pd.to_numeric(self.df["views"], errors="coerce").fillna(0)
        
        # Chuẩn hóa views về [0,1] để dễ kết hợp với score
        max_views = self.df["views"].max()
        self.df["views_norm"] = self.df["views"] / max_views if max_views > 0 else 0
        
        self.model = SentenceTransformer("keepitreal/vietnamese-sbert")
        self.corpus_embeddings = self.load_embeddings()

    def load_embeddings(self):
        try:
            embeddings = torch.load("food_embeddings.pt")
            return embeddings
        except FileNotFoundError:
            corpus = (self.df["ten_mon"] + " " + self.df["ingredients"]).tolist()
            embeddings = self.model.encode(corpus, convert_to_tensor=True, show_progress_bar=True)
            torch.save(embeddings, "food_embeddings.pt")
            return embeddings

    def keyword_overlap(self, query: str, text: str) -> float:
        query_tokens = set(re.findall(r"\w+", query.lower()))
        text_tokens = set(re.findall(r"\w+", text.lower()))
        if not query_tokens:
            return 0.0
        return len(query_tokens & text_tokens) / len(query_tokens)

    def recommend_food(self, query: str, top_k: int = 5, alpha: float = 0.7, beta: float = 0.1):
        """
        alpha: trọng số giữa similarity và keyword overlap
        beta: trọng số của views (ưu tiên món được xem nhiều)
        """
        query_embedding = self.model.encode(query, convert_to_tensor=True)
        cos_scores = util.cos_sim(query_embedding, self.corpus_embeddings)[0]
        top_results = torch.topk(cos_scores, k=top_k * 5)

        results = []
        for score, idx in zip(top_results[0], top_results[1]):
            row = self.df.iloc[idx.item()]
            text = f"{row['ten_mon']} {row['ingredients']}"
            kw_score = self.keyword_overlap(query, text)

            # Tính điểm tổng hợp có thêm ảnh hưởng của views
            base_score = alpha * float(score) + (1 - alpha) * kw_score
            final_score = base_score * (1 - beta) + beta * row["views_norm"]

            results.append({
                "id": int(row.get("id", 0)) if pd.notna(row.get("id", 0)) else 0,
                "ten_mon": row.get("ten_mon", ""),
                "ingredients": row.get("ingredients", ""),
                "link": row.get("link", ""),
                "anh": row.get("anh", ""),
                "mo_ta": row.get("mo_ta", ""),
                "ready_html": row.get("ready_html", ""),
                "step_html": row.get("step_html", ""),
                "category": row.get("category", ""),
                "views": int(row.get("views", 0)),
                "similarity": float(score),
                "keyword_score": kw_score,
                "views_norm": float(row["views_norm"]),
                "final_score": float(final_score)
            })

        # Sắp xếp theo điểm tổng hợp
        results = sorted(results, key=lambda x: x["final_score"], reverse=True)[:top_k]
        return results


# Hàm tiện ích gọi từ API
recommender = Recommender()

def recommend_food(query, top_k=5, alpha=0.7, beta=0.1):
    return recommender.recommend_food(query, top_k, alpha, beta)
