from __future__ import annotations

import uuid
from pathlib import Path
import hashlib

import chromadb
import numpy as np

from .config import config
from .ingestion import Chunk


class LocalHashEmbeddingFunction:
    def __init__(self, dimension: int = 384) -> None:
        self.dimension = dimension

    def name(self) -> str:
        return "local_hash_v1"

    def __call__(self, input: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in input:
            vec = np.zeros(self.dimension, dtype=np.float32)
            tokens = text.lower().split()
            for tok in tokens:
                h = hashlib.md5(tok.encode("utf-8")).hexdigest()
                idx = int(h, 16) % self.dimension
                vec[idx] += 1.0
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            vectors.append(vec.tolist())
        return vectors


class VectorStore:
    def __init__(self) -> None:
        config.chroma_dir.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(config.chroma_dir))
        embedding_fn = LocalHashEmbeddingFunction()
        try:
            self.collection = self.client.get_or_create_collection(
                name="arvinds_bot_kb",
                embedding_function=embedding_fn,
                metadata={"hnsw:space": "cosine"},
            )
        except ValueError as e:
            msg = str(e).lower()
            if "embedding function conflict" in msg:
                # One-time migration path when switching embedding functions.
                self.client.delete_collection("arvinds_bot_kb")
                self.collection = self.client.get_or_create_collection(
                    name="arvinds_bot_kb",
                    embedding_function=embedding_fn,
                    metadata={"hnsw:space": "cosine"},
                )
            else:
                raise

    def clear(self) -> None:
        self.client.delete_collection("arvinds_bot_kb")
        embedding_fn = LocalHashEmbeddingFunction()
        self.collection = self.client.get_or_create_collection(
            name="arvinds_bot_kb",
            embedding_function=embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert_chunks(self, chunks: list[Chunk]) -> int:
        if not chunks:
            return 0
        ids = [str(uuid.uuid4()) for _ in chunks]
        docs = [c.text for c in chunks]
        metadatas = [{"source": c.source} for c in chunks]
        self.collection.add(ids=ids, documents=docs, metadatas=metadatas)
        return len(chunks)

    def search(self, query: str, top_k: int = 6) -> dict:
        return self.collection.query(
            query_texts=[query],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

    def count(self) -> int:
        return self.collection.count()


def list_docx_files(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        p = Path(raw).expanduser()
        if p.is_file() and p.suffix.lower() == ".docx":
            files.append(p)
        elif p.is_dir():
            files.extend(sorted(x for x in p.rglob("*.docx") if x.is_file()))
    return files
