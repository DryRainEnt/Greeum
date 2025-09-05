#!/usr/bin/env python3
"""
Greeum CLI entry point for python -m greeum
"""

def main():
    """CLI 진입점"""
    try:
        from greeum.cli import main as cli_main
        cli_main()
    except ImportError:
        # Fallback to basic version info
        from greeum import __version__
        print(f"Greeum {__version__}")

if __name__ == "__main__":
    main()