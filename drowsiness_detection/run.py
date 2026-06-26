#!/usr/bin/env python3
"""Run from the project root:  python run.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))
from main import main
if __name__ == "__main__":
    sys.exit(main())
