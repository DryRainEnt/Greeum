"""
Greeum API Server - CLI Entry Point

Run with: python -m greeum.server
Or: greeum-server (after installing with pip)
"""

import argparse
import uvicorn

from .config import config


def main():
    """Main entry point for the server."""
    parser = argparse.ArgumentParser(
        description="Greeum API Server",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--host",
        type=str,
        default=config.host,
        help="Host to bind to",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=config.port,
        help="Port to bind to",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=config.log_level.lower(),
        choices=["debug", "info", "warning", "error"],
        help="Log level",
    )

    args = parser.parse_args()

    print(f"""
╔═══════════════════════════════════════════════════════════╗
║                    Greeum API Server                      ║
║                       v4.0.0                              ║
╠═══════════════════════════════════════════════════════════╣
║  Endpoints:                                               ║
║    • GET  /health        - Health check                   ║
║    • POST /memory        - Add memory                     ║
║    • GET  /memory/{{id}}   - Get memory                    ║
║    • POST /search        - Search memories                ║
║    • GET  /stats         - Get statistics                 ║
║    • GET  /docs          - Swagger UI                     ║
╠═══════════════════════════════════════════════════════════╣
║  Server: http://{args.host}:{args.port}                          ║
╚═══════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        "greeum.server.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level,
    )


if __name__ == "__main__":
    main()
