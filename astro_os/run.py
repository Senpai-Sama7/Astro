#!/usr/bin/env python3
"""Astro-OS launcher."""
import sys
import os

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from astro_os.main import main

if __name__ == "__main__":
    main()
