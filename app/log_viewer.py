#!/usr/bin/env python3
import json
import sys
import time
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

_TZ_LAB = ZoneInfo("America/Sao_Paulo")

# ANSI colors
R  = "\033[31m"  # red
G  = "\033[32m"  # green
Y  = "\033[33m"  # yellow
B  = "\033[34m"  # blue
M  = "\033[35m"  # magenta
C  = "\033[36m"  # cyan
W  = "\033[37m"  # white
DIM = "\033[2m"
RST = "\033[0m"

RED_ACTIONS    = {"BLOCKED", "REDACTED", "UNSAFE", "ERROR"}
GREEN_ACTIONS  = {"PASSED", "SAFE", "CLEAN"}
MCP_SRCS       = {"MCP"}
RAG_SRCS       = {"RAG"}
MAGENTA_SRCS   = {"D3", "D4"}
CHAT_SRCS      = {"CHAT"}
APP_SRCS       = {"APP"}


def color_for(src: str, action: str) -> str:
    if action in RED_ACTIONS:
        return R
    if action in GREEN_ACTIONS:
        return G
    if src in MCP_SRCS:
        return B
    if src in RAG_SRCS:
        return Y
    if src in MAGENTA_SRCS:
        return M
    if src in CHAT_SRCS:
        return C
    return W


def format_line(entry: dict) -> str:
    try:
        ts  = datetime.fromisoformat(entry["ts"]).astimezone(_TZ_LAB).strftime("%H:%M:%S")
        rid = entry.get("request_id", "--------")
        src = entry.get("src", "")
        act = entry.get("action", "")
        det = entry.get("detail", "")
        ms  = entry.get("elapsed_ms", 0.0)
    except (KeyError, ValueError):
        return f"{W}{entry}{RST}"

    col   = color_for(src, act)
    ms_s  = f" ({ms:.0f}ms)" if ms else ""
    det_s = f' | "{det}"' if det else ""

    return f"{col}{ts} {rid} | {src:4} | {act}{det_s}{ms_s}{RST}"


def pick_log_file() -> Path:
    logs_dir = Path(__file__).parent / "logs"
    files = sorted(logs_dir.glob("*.jsonl"))
    if not files:
        print(f"Nenhum arquivo .jsonl encontrado em {logs_dir}", file=sys.stderr)
        sys.exit(1)
    return files[-1]


def tail_f(path: Path) -> None:
    print(f"{DIM}→ {path}{RST}\n")
    # Como cada startup gera um arquivo de log novo (timestamp + sufixo
    # aleatório em logger.py), este arquivo contém SOMENTE o log desta
    # execução. Vamos do início para pegar tudo desde o boot — incluindo
    # o ensure_indexed() do RAG, que ocorre antes do entrypoint detectar
    # o socket e iniciar este tail.
    with path.open(encoding="utf-8") as f:
        f.seek(0, 0)  # go to start
        while True:
            line = f.readline()
            if line:
                line = line.strip()
                if line:
                    try:
                        entry = json.loads(line)
                        print(format_line(entry))
                    except json.JSONDecodeError:
                        print(f"{R}[parse error]{RST} {line}")
            else:
                time.sleep(0.1)


def replay(path: Path) -> None:
    print(f"{DIM}→ {path}{RST}\n")
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                print(format_line(entry))
            except json.JSONDecodeError:
                print(f"{R}[parse error]{RST} {line}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        log_path = Path(sys.argv[1])
    else:
        log_path = pick_log_file()

    if not log_path.exists():
        print(f"Arquivo não encontrado: {log_path}", file=sys.stderr)
        sys.exit(1)

    try:
        tail_f(log_path)
    except KeyboardInterrupt:
        print(f"\n{DIM}encerrado{RST}")
