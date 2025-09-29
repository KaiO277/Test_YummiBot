from sentence_transformers import SentenceTransformer
import torch
import pandas as pd
import os

class EmbeddingManager:
    def __init__(self, model_name: str, data_file: str, embedding_file: str):
        self.model_name = model_name
        self.data_file = data_file
        self.embedding_file = embedding_file
        self.model = SentenceTransformer(self.model_name)
        self.corpus_embeddings = self.load_embeddings()

    def load_embeddings(self):
        if os.path.exists(self.embedding_file):
            print("✅ Loaded embeddings from file", self.embedding_file)
            return torch.load(self.embedding_file)
        else:
            print("⚠️ Embeddings not found, encoding new embeddings...")
            df = pd.read_csv(self.data_file)
            df = df.dropna(subset=["ingredients", "ten_mon"])
            corpus = (df["ten_mon"] + " " + df["ingredients"]).tolist()
            corpus_embeddings = self.model.encode(corpus, convert_to_tensor=True, show_progress_bar=True)
            torch.save(corpus_embeddings, self.embedding_file)
            print("✅ Saved embeddings to", self.embedding_file)
            return corpus_embeddings

    def get_embeddings(self):
        return self.corpus_embeddings