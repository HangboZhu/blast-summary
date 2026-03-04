#!/usr/bin/env python3
"""
BLAST Summary Tool - 外部入口脚本

用法:
    python main.py data/blastp/blastp_example.txt
    python main.py --help
"""

import sys
from blast_summary.cli import main

if __name__ == "__main__":
    sys.exit(main())
