#!/usr/bin/env python3
"""
Script to export procedures from database to Excel.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from apps.export.to_excel import export_from_db
from apps.orchestrator.config import settings

if __name__ == "__main__":
    output_path = sys.argv[1] if len(sys.argv) > 1 else "bess_procedures.xlsx"
    filter_high = "--high-only" in sys.argv
    
    print(f"Exporting procedures to {output_path}...")
    export_from_db(
        db_dsn=settings.postgres_dsn,
        output_path=output_path,
        filter_high_confidence=filter_high,
    )
    print("Done!")







