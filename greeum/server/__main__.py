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

    auth_status = "Enabled (X-API-Key)" if config.auth_enabled else "Disabled (open access)"

    print(f"""
╔═══════════════════════════════════════════════════════════╗
║                    Greeum API Server                      ║
║                       v5.0.0                              ║
╠═══════════════════════════════════════════════════════════╣
║  Features:                                                ║
║    • InsightJudge LLM-based filtering                     ║
║    • API Key authentication (optional)                    ║
║    • STM slot management                                  ║
╠═══════════════════════════════════════════════════════════╣
║  Endpoints:                                               ║
║    • GET  /health        - Health check                   ║
║    • POST /memory        - Add memory (InsightJudge)      ║
║    • GET  /memory/{{id}}   - Get memory                    ║
║    • POST /search        - Search memories                ║
║    • GET  /stats         - Get statistics                 ║
║    • GET  /stm/slots     - STM slot status                ║
║    • GET  /docs          - Swagger UI                     ║
╠═══════════════════════════════════════════════════════════╣
║  Auth: {auth_status:<42}  ║
║  Server: http://{args.host}:{args.port:<38}  ║
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
