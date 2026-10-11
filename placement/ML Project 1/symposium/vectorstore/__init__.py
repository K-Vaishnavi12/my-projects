"""Vector-store package.

Two backends behind a single :class:`VectorStore` interface:

- :class:`MongoAtlasStore`  - uses ``$vectorSearch`` on Atlas Search.
- :class:`LocalFaissStore`  - falls back to FAISS for offline dev.

The chosen backend is picked at import time based on
``settings.use_local_vector_store``. Consumers should import the
factory only::

    from symposium.vectorstore.base import RetrievedChunk, VectorStore
    from symposium.vectorstore.factory import get_vector_store
"""

from symposium.vectorstore.base import RetrievedChunk, VectorStore

__all__ = ["RetrievedChunk", "VectorStore"]
