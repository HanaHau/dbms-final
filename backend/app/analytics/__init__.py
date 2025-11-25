# analytics/__init__.py
from .patient_analysis import get_patient_statistics, get_duckdb_conn

__all__ = ["get_patient_statistics", "get_duckdb_conn"]

