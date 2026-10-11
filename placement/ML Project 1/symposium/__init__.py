"""Symposium: A multi-agent debating RAG.

This is the top-level package. The public API is intentionally tiny;
subpackages hold the real logic:

- ``symposium.config``      - typed settings + persona registry
- ``symposium.etl``         - extract / transform / load
- ``symposium.dwh``         - SQL data-warehouse layer
- ``symposium.vectorstore`` - MongoDB + vector search
- ``symposium.ml``          - classical ML + neural net
- ``symposium.agents``      - persona agents + moderator + orchestrator
- ``symposium.prompts``     - prompt-engineering templates
- ``symposium.utils``       - advanced Python showcase + helpers
"""

__version__ = "1.0.0"
__all__ = ["__version__"]
