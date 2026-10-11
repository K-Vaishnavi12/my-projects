"""Transform stage.

Individual utilities live in submodules; import what you need
directly to keep lightweight callers (like the ML tests or the
persona classifier) free of heavy dependencies:

    from symposium.etl.transform.cleaner import clean_article
    from symposium.etl.transform.persona_classifier import score_chunk_for_personas
    from symposium.etl.transform.chunker import chunk_article
    from symposium.etl.transform.embedder import get_embedder
"""
