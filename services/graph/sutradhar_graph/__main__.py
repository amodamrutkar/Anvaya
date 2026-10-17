"""
CLI entry point for Sutradhar Graph and Network Analytics.

Usage: python -m sutradhar_graph.run --data data/v1 --er artifacts/er --out artifacts/graph
"""

from .run import main

if __name__ == "__main__":
    main()
