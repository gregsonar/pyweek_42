#!/usr/bin/env python3
import os
import sys

if getattr(sys, "frozen", False):
    os.chdir(sys._MEIPASS)
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")

from src.main import run_engine

if __name__ == "__main__":
    run_engine()
