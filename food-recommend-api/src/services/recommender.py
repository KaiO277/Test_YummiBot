from fastapi import HTTPException
import pandas as pd
from sentence_transformers import SentenceTransformer, util
import torch
import re

class Recommender:
    def __init__(self):
        self.df = pd.read_csv("merged_data.csv")
        self.df = self.df.dropna(subset=["ingredients", "ten_mon"])
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

    def recommend_food(self, query: str, top_k: int = 5, alpha: float = 0.7):
        query_embedding = self.model.encode(query, convert_to_tensor=True)
        cos_scores = util.cos_sim(query_embedding, self.corpus_embeddings)[0]
        top_results = torch.topk(cos_scores, k=top_k * 3)

        results = []
        for score, idx in zip(top_results[0], top_results[1]):
            row = self.df.iloc[idx.item()]
            text = f"{row['ten_mon']} {row['ingredients']}"
            kw_score = self.keyword_overlap(query, text)
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

recommender = Recommender()

def recommend_food(query, top_k=5, alpha=0.7):
    return recommender.recommend_food(query, top_k, alpha)