import os
import random
import socket
import struct
from typing import Dict, Optional

from fastapi import FastAPI

DEFAULT_HOST = "nwn-ee-pw"
DEFAULT_PORT = 5121
DEFAULT_TIMEOUT = 2.0
MAX_PACKET_SIZE = 4096

app = FastAPI()


def _get_target() -> tuple[str, int]:
    host = os.getenv("NWN_HOST", DEFAULT_HOST)
    port_raw = os.getenv("NWN_PORT", str(DEFAULT_PORT))
    try:
        port = int(port_raw)
    except ValueError:
        port = DEFAULT_PORT

    if not 1 <= port <= 65535:
        port = DEFAULT_PORT

    return host, port


def _safe_int(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _parse_kv_null(data: bytes) -> Dict[str, str]:
    if not data:
        return {}

    if b"\x00\x00" in data:
        data = data.split(b"\x00\x00", 1)[0]

    parts = data.split(b"\x00")
    kv: Dict[str, str] = {}
    for i in range(0, len(parts) - 1, 2):
        key = parts[i].decode("latin-1", "replace")
        value = parts[i + 1].decode("latin-1", "replace")
        if key:
            kv[key] = value
    return kv


def _parse_kv_backslash(data: bytes) -> Dict[str, str]:
    parts = [part for part in data.split(b"\\") if part]
    kv: Dict[str, str] = {}
    for i in range(0, len(parts) - 1, 2):
        key = parts[i].decode("latin-1", "replace")
        if key.lower() == "final":
            break
        value = parts[i + 1].decode("latin-1", "replace")
        kv[key] = value
    return kv


def _query_gamespy3(host: str, port: int, timeout: float) -> Optional[Dict[str, str]]:
    session_id = random.randint(0, 0xFFFFFFFF)
    session_bytes = struct.pack(">I", session_id)
    addr = (host, port)

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(timeout)
        sock.sendto(b"\xFE\xFD\x09" + session_bytes, addr)
        try:
            response = sock.recvfrom(MAX_PACKET_SIZE)[0]
        except socket.timeout:
            return None

        if len(response) < 5 or response[0:1] != b"\x09":
            return None

        challenge_raw = response[5:].split(b"\x00", 1)[0].strip()
        if not challenge_raw:
            return None

        try:
            challenge_int = int(challenge_raw)
        except ValueError:
            return None

        try:
            challenge_bytes = struct.pack(">i", challenge_int)
        except struct.error:
            return None

        sock.sendto(
            b"\xFE\xFD\x00" + session_bytes + challenge_bytes + b"\x00\x00\x00\x00",
            addr,
        )
        try:
            response = sock.recvfrom(MAX_PACKET_SIZE)[0]
        except socket.timeout:
            return None

        if len(response) < 5 or response[0:1] != b"\x00":
            return None

    return _parse_kv_null(response[5:])


def _query_gamespy2(host: str, port: int, timeout: float) -> Optional[Dict[str, str]]:
    addr = (host, port)
    for payload in (b"\\status\\", b"\\basic\\"):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(timeout)
            sock.sendto(payload, addr)
            try:
                response = sock.recvfrom(MAX_PACKET_SIZE)[0]
            except socket.timeout:
                continue

        if response:
            return _parse_kv_backslash(response)

    return None


def _format_status(kv: Dict[str, str]) -> dict:
    kv_lower = {key.lower(): value for key, value in kv.items()}

    name = (
        kv_lower.get("hostname")
        or kv_lower.get("name")
        or kv_lower.get("sv_hostname")
    )

    players = _safe_int(
        kv_lower.get("numplayers")
        or kv_lower.get("num_players")
        or kv_lower.get("clients")
        or kv_lower.get("players")
    )

    max_players = _safe_int(
        kv_lower.get("maxplayers")
        or kv_lower.get("max_clients")
        or kv_lower.get("sv_maxplayers")
    )

    if players is None or players < 0:
        players = 0

    if max_players is not None and max_players < 0:
        max_players = None

    return {
        "online": True,
        "players": players,
        "max_players": max_players,
        "name": name,
    }


def _query_status(host: str, port: int) -> dict:
    for query in (_query_gamespy3, _query_gamespy2):
        try:
            kv = query(host, port, DEFAULT_TIMEOUT)
        except OSError:
            kv = None
        if kv is not None:
            return _format_status(kv)

    return {
        "online": False,
        "players": 0,
        "max_players": None,
        "name": None,
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/status")
def status() -> dict:
    host, port = _get_target()
    return _query_status(host, port)
