#!/usr/bin/env python3
"""
Greeum Memory Visualization Server
독립 실행 가능한 시각화 서버

사용법:
    python -m greeum.viz.server
    python -m greeum.viz.server --port 8401
    python -m greeum.viz.server --db-path /path/to/memory.db
"""

import argparse
import os
import sys
import webbrowser
from pathlib import Path

# uvicorn 설치 확인
try:
    import uvicorn
except ImportError:
    print("Error: uvicorn이 설치되지 않았습니다.")
    print("  pip install uvicorn")
    sys.exit(1)

try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import HTMLResponse
except ImportError:
    print("Error: FastAPI가 설치되지 않았습니다.")
    print("  pip install fastapi")
    sys.exit(1)

from .api import VisualizationDataProvider, create_viz_router


def create_app(db_path: str = None) -> FastAPI:
    """FastAPI 앱 생성"""
    app = FastAPI(
        title="Greeum Memory Visualization",
        description="기억 데이터 시각화 서버",
        version="1.0.0"
    )

    # CORS 설정
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # DB 경로 설정
    if db_path:
        os.environ["GREEUM_VIZ_DB_PATH"] = db_path

    # 시각화 라우터 추가
    viz_router = create_viz_router()
    if viz_router:
        app.include_router(viz_router)

    # 루트 리다이렉트
    @app.get("/", response_class=HTMLResponse)
    async def root():
        return """
        <html>
        <head>
            <meta http-equiv="refresh" content="0; url=/viz/" />
        </head>
        <body>
            <p>Redirecting to <a href="/viz/">Visualization</a>...</p>
        </body>
        </html>
        """

    return app


def main():
    parser = argparse.ArgumentParser(
        description="Greeum Memory Visualization Server"
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8401,
        help="서버 포트 (기본: 8401)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="서버 호스트 (기본: 127.0.0.1)"
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default=None,
        help="데이터베이스 경로 (기본: 자동 탐색)"
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="브라우저 자동 열기 비활성화"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="개발 모드 (자동 리로드)"
    )

    args = parser.parse_args()

    # 앱 생성
    app = create_app(args.db_path)

    # 서버 시작 메시지
    url = f"http://{args.host}:{args.port}"
    viz_url = f"{url}/viz/"
    print(f"""
╔══════════════════════════════════════════════════════════╗
║           🌳 Greeum Memory Visualization                 ║
╠══════════════════════════════════════════════════════════╣
║  Server:  {url}                                          ║
║  Graph:   {viz_url}                                      ║
╚══════════════════════════════════════════════════════════╝
    """)

    # 브라우저 열기
    if not args.no_browser:
        webbrowser.open(f"{url}/viz/")

    # 서버 실행
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info"
    )


if __name__ == "__main__":
    main()
