"""Data warehouse package.

Ships:
- SQL DDL / DML / views / triggers / stored-procedure-equivalent functions
- A thin :class:`Warehouse` accessor for the Streamlit UI
"""

from symposium.dwh.warehouse import Warehouse

__all__ = ["Warehouse"]
