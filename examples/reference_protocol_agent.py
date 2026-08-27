from __future__ import annotations

import argparse
from http.server import ThreadingHTTPServer

from observer.reference_protocol_agent import (
    ReferenceProtocolAgent,
)
from observer.reference_protocol_agent_http import (
    make_reference_protocol_handler,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the DLLO reference Agent Protocol "
            "1.0 SUT."
        ),
    )

    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Bind host; localhost only",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="TCP port",
    )

    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.host not in {
        "127.0.0.1",
        "::1",
        "localhost",
    }:
        raise SystemExit(
            "Reference protocol agent may only bind "
            "to localhost."
        )

    agent = ReferenceProtocolAgent()

    server = ThreadingHTTPServer(
        (args.host, args.port),
        make_reference_protocol_handler(agent),
    )

    host, port = server.server_address

    print(
        "DLLO Reference Protocol Agent "
        f"listening on http://{host}:{port}"
    )

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
