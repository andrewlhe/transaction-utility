#!/usr/bin/env python3
"""Transaction Utility - main entry point.

Launches the Tkinter GUI for transaction settlement (CSV/XLSX).
Other tools live under ``apps/`` as separate programs.
"""
import sys
from transaction_utility.gui import main

if __name__ == "__main__":
    sys.exit(main() or 0)
