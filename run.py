from __future__ import annotations

from app import build_server


if __name__ == "__main__":
    server = build_server()
    print(f"Serving on http://{server.server_address[0]}:{server.server_address[1]}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
