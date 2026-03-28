#!/usr/bin/env python3
"""Single startup file for the NMBS dashboard application."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _add_src_to_path() -> None:
    project_root = Path(__file__).resolve().parent
    src_path = project_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))


def main() -> None:
    _add_src_to_path()

    from nmbs_dashboard.app import create_dash_app

    parser = argparse.ArgumentParser(description="NMBS dashboard startup")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host")
    parser.add_argument("--port", type=int, default=8050, help="Bind port")
    parser.add_argument("--debug", action="store_true", help="Enable Dash debug mode")
    args = parser.parse_args()

    app = create_dash_app()
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()