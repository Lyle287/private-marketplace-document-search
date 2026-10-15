import json
import math
import sqlite3
from collections.abc import Sequence
from typing import Protocol

from .models import AssetKind, MarketplaceDocument, SearchHit


class Embedder(Protocol):
    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        return []


class MarketplaceIndex:
    def __init__(self, database: str, embedder: Embedder) -> None:
        self._connection = sqlite3.connect(database, check_same_thread=False)
        self._embedder = embedder
        self._connection.execute(
            """CREATE TABLE IF NOT EXISTS documents (
                document_id TEXT PRIMARY KEY,
                kind TEXT NOT NULL,
                seller_id TEXT NOT NULL,
                buyer_id TEXT,
                order_id TEXT,
                text TEXT NOT NULL,
                embedding TEXT NOT NULL
            )"""
        )

    def add(self, documents: list[MarketplaceDocument]) -> int:
        vectors = self._embedder.embed([document.text for document in documents])
        if len(vectors) != len(documents):
            raise ValueError("embedding count does not match document count")
        with self._connection:
            for document, vector in zip(documents, vectors, strict=True):
                self._connection.execute(
                    """INSERT OR REPLACE INTO documents
                    (document_id, kind, seller_id, buyer_id, order_id, text, embedding)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        document.document_id,
                        document.kind.value,
                        document.seller_id,
                        document.buyer_id,
                        document.order_id,
                        document.text,
                        json.dumps(vector),
                    ),
                )
        return len(documents)

    def search(
        self, query: str, buyer_id: str, seller_id: str | None, limit: int
    ) -> list[SearchHit]:
        query_vector = self._embedder.embed([query])[0]
        sql = """SELECT document_id, kind, text, embedding FROM documents
                 WHERE (kind = ? OR buyer_id = ?)"""
        parameters: list[str] = [AssetKind.SELLER_ASSET.value, buyer_id]
        if seller_id:
            sql += " AND seller_id = ?"
            parameters.append(seller_id)
        rows = self._connection.execute(sql, parameters).fetchall()
        hits = [
            SearchHit(
                document_id=row[0],
                kind=AssetKind(row[1]),
                text=row[2],
                score=self._cosine(query_vector, json.loads(row[3])),
            )
            for row in rows
        ]
        return sorted(hits, key=lambda hit: (-hit.score, hit.document_id))[:limit]

    @staticmethod
    def _cosine(left: list[float], right: list[float]) -> float:
        if len(left) != len(right):
            raise ValueError("embedding dimensions do not match")
        denominator = math.sqrt(sum(x * x for x in left)) * math.sqrt(
            sum(x * x for x in right)
        )
        return sum(x * y for x, y in zip(left, right, strict=True)) / denominator if denominator else 0.0
