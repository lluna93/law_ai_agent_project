
import torch
from sentence_transformers import SentenceTransformer


class GPUEmbeddings:
    def __init__(self):
        self.device = (
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        print(f"[Embedding] Device: {self.device}")

        if self.device == "cuda":
            print(
                "[Embedding] GPU:",
                torch.cuda.get_device_name(0)
            )

        self.model = SentenceTransformer(
            "intfloat/multilingual-e5-small",
            device=self.device,
        )

        self.dimension = (
            self.model.get_sentence_embedding_dimension()
        )

        print(
            f"[Embedding] Dimension: {self.dimension}"
        )

    def embed_documents(self, texts):
        texts = [
            f"passage: {text}" for text in texts
        ]

        vectors = self.model.encode(
            texts,
            batch_size=16,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=True,
        )

        return vectors.tolist()

    def embed_query(self, text):
        vector = self.model.encode(
            f"query: {text}",
            normalize_embeddings=True,
            convert_to_numpy=True,
        )

        return vector.tolist()
