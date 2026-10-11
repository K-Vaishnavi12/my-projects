"""MongoDB loader.

Writes chunks into per-persona collections plus a global collection.
Per-persona collections let us keep vector-search indexes tightly
scoped so each agent retrieves ONLY from its own worldview.

Collections created:
- ``documents``                    : one row per source article
- ``chunks_all``                   : every chunk (canonical store)
- ``chunks_<persona_key>``         : chunks whose persona affinity >= threshold

The vector index is created programmatically via
:meth:`ensure_vector_index` (Atlas Search API).
"""

from __future__ import annotations

from typing import Any, Iterable

from loguru import logger
from pymongo import ASCENDING, MongoClient, UpdateOne
from pymongo.collection import Collection

from symposium.config import get_settings
from symposium.config.personas import PERSONAS


class MongoLoader:
    """One-stop MongoDB write helper."""

    PERSONA_AFFINITY_THRESHOLD = 0.60  # chunk is claimed by a persona if score >= this
    VECTOR_INDEX_NAME = "vector_index"

    def __init__(self, uri: str | None = None, db: str | None = None) -> None:
        s = get_settings()
        self.client = MongoClient(uri or s.mongodb_uri)
        self.db = self.client[db or s.mongodb_db]

    # --------------------------------------------------------------
    # Setup
    # --------------------------------------------------------------

    def ensure_collections(self) -> None:
        """Create collections + basic (non-vector) indexes if missing."""
        names = set(self.db.list_collection_names())
        wanted = {"documents", "chunks_all"} | {
            f"chunks_{k}" for k in PERSONAS.keys()
        }
        for name in wanted - names:
            self.db.create_collection(name)
            logger.info(f"[mongo] created collection {name}")

        # traditional (non-vector) indexes
        self.db["documents"].create_index([("id", ASCENDING)], unique=True)
        for name in wanted:
            if name == "documents":
                continue
            self.db[name].create_index([("chunk_id", ASCENDING)], unique=True)
            self.db[name].create_index([("topic", ASCENDING)])
            self.db[name].create_index([("doc_id", ASCENDING)])

    def ensure_vector_index(self) -> None:
        """Create Atlas Search vector indexes on every chunk collection.

        Silently no-ops on non-Atlas deployments (community edition
        does not support ``createSearchIndex``) so local dev still works.
        """
        names = ["chunks_all"] + [f"chunks_{k}" for k in PERSONAS.keys()]
        for name in names:
            coll = self.db[name]
            try:
                existing = list(coll.list_search_indexes())
                if any(ix["name"] == self.VECTOR_INDEX_NAME for ix in existing):
                    continue
                coll.create_search_index(
                    {
                        "name": self.VECTOR_INDEX_NAME,
                        "definition": {
                            "mappings": {
                                "dynamic": False,
                                "fields": {
                                    "embedding": {
                                        "type": "knnVector",
                                        "dimensions": get_settings().embedding_dim,
                                        "similarity": "cosine",
                                    }
                                },
                            }
                        },
                    }
                )
                logger.info(f"[mongo] vector index created on {name}")
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    f"[mongo] could not create vector index on {name} "
                    f"(likely non-Atlas deployment): {exc}"
                )

    # --------------------------------------------------------------
    # Writes
    # --------------------------------------------------------------

    def upsert_document(self, article: dict[str, Any]) -> None:
        doc = {
            "id": article["id"],
            "title": article["title"],
            "url": article.get("url"),
            "topic": article.get("topic"),
            "summary": article.get("summary"),
            "categories": article.get("categories", []),
            "extracted_at": article.get("extracted_at"),
        }
        self.db["documents"].update_one(
            {"id": doc["id"]}, {"$set": doc}, upsert=True
        )

    def upsert_chunks(
        self,
        chunks: Iterable[dict[str, Any]],
        embeddings: Iterable[list[float]],
    ) -> int:
        """Bulk-upsert chunks + fan them out to per-persona collections."""
        chunks_list = list(chunks)
        embeddings_list = list(embeddings)
        if len(chunks_list) != len(embeddings_list):
            raise ValueError("chunks / embeddings length mismatch")

        # attach embedding to chunk
        for c, emb in zip(chunks_list, embeddings_list):
            c["embedding"] = emb

        # global collection
        self._bulk_upsert("chunks_all", chunks_list, key="chunk_id")

        # persona-scoped collections
        for pkey in PERSONAS.keys():
            claimed = [
                c for c in chunks_list
                if c["persona_scores"].get(pkey, 0.0) >= self.PERSONA_AFFINITY_THRESHOLD
            ]
            if claimed:
                self._bulk_upsert(f"chunks_{pkey}", claimed, key="chunk_id")
                logger.info(
                    f"[mongo] persona '{pkey}': {len(claimed)} chunks claimed"
                )
        return len(chunks_list)

    def _bulk_upsert(
        self, collection: str, docs: list[dict[str, Any]], key: str
    ) -> None:
        if not docs:
            return
        coll: Collection = self.db[collection]
        ops = [
            UpdateOne({key: d[key]}, {"$set": d}, upsert=True) for d in docs
        ]
        result = coll.bulk_write(ops, ordered=False)
        logger.info(
            f"[mongo] {collection}: upserted={result.upserted_count} "
            f"modified={result.modified_count} matched={result.matched_count}"
        )

    # --------------------------------------------------------------
    # Reads (used by vectorstore.search)
    # --------------------------------------------------------------

    def collection(self, name: str) -> Collection:
        return self.db[name]

    def close(self) -> None:
        self.client.close()
