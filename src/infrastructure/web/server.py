"""Uvicorn-in-thread runner for the dashboard."""
import threading

import uvicorn
from fastapi import FastAPI

from domain.ports.logger import AppLogger


def run_in_thread(app: FastAPI, host: str, port: int, logger: AppLogger) -> threading.Thread:
    """Starts Uvicorn for `app` in a daemon thread and returns it.

    The thread is daemonised so the process exits cleanly when the
    scheduler's main loop returns; no explicit graceful shutdown is needed.
    """
    config = uvicorn.Config(app, host=host, port=port, log_level="warning", access_log=False)
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, name="dashboard-uvicorn", daemon=True)
    thread.start()

    logger.info(f"Dashboard listening on http://{host}:{port}")
    return thread
