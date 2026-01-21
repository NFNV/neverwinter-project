import http.client
import json
import os
import socket
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI

DEFAULT_CONTAINER_NAME = "nwn-ee-pw"
DEFAULT_DOCKER_SOCK = "/var/run/docker.sock"

app = FastAPI()


def _get_container_name() -> str:
    name = os.getenv("NWN_CONTAINER_NAME", DEFAULT_CONTAINER_NAME).strip()
    return name or DEFAULT_CONTAINER_NAME


def _get_docker_sock() -> str:
    sock = os.getenv("DOCKER_SOCK", DEFAULT_DOCKER_SOCK).strip()
    return sock or DEFAULT_DOCKER_SOCK


def _utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _docker_unix_get_json(sock_path: str, path: str, timeout: float = 2.0) -> tuple[int, Optional[dict]]:
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    sock.connect(sock_path)
    try:
        request = (
            f"GET {path} HTTP/1.1\r\n"
            "Host: localhost\r\n"
            "Connection: close\r\n"
            "\r\n"
        ).encode("utf-8")
        sock.sendall(request)
        response = http.client.HTTPResponse(sock)
        response.begin()
        body = response.read()
        if not body:
            return response.status, None
        try:
            payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            payload = None
        return response.status, payload
    finally:
        try:
            sock.close()
        except OSError:
            pass


def _check_container(container_name: str, sock_path: str) -> tuple[bool, Optional[str], Optional[str]]:
    try:
        status, data = _docker_unix_get_json(
            sock_path,
            f"/containers/{container_name}/json",
        )
    except (OSError, http.client.HTTPException) as exc:
        return False, None, f"{exc.__class__.__name__}: {exc}"

    if status == 200 and isinstance(data, dict):
        state = data.get("State", {})
        running = bool(state.get("Running", False))
        return running, state.get("Status"), None
    if status == 404:
        return False, None, "container_not_found"
    return False, None, f"http_{status}"


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/status")
def status() -> dict:
    container_name = _get_container_name()
    sock_path = _get_docker_sock()
    running, state, error = _check_container(container_name, sock_path)
    response = {
        "online": running,
        "server_running": running,
        "players": 0,
        "max_players": None,
        "name": None,
        "container_state": state,
        "checked_at": _utc_now(),
    }
    if error:
        response["docker_error"] = error
    return response
