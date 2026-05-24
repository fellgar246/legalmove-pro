import logging
import signal
import sys
import time

from config import DATABASE_URL, WORKER_POLL_INTERVAL_SECONDS, langfuse_enabled, validate
from db import get_connection
from worker import run_once

_running = True


def _shutdown(signum, frame) -> None:
    global _running
    print(f"[worker] received signal {signum}, shutting down...")
    _running = False


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    validate()

    if langfuse_enabled():
        print("[worker] Langfuse observability enabled")
    else:
        print("[worker] Langfuse disabled (missing LANGFUSE_* env vars)")

    conn = get_connection(DATABASE_URL)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    print(f"[worker] started, poll interval={WORKER_POLL_INTERVAL_SECONDS}s")
    while _running:
        try:
            run_once(conn)
        except Exception as e:
            print(f"[worker] unexpected error: {e}")
        time.sleep(WORKER_POLL_INTERVAL_SECONDS)

    conn.close()
    print("[worker] stopped")
    sys.exit(0)


if __name__ == "__main__":
    main()
