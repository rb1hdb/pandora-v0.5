import json
import secrets
import uuid
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

_TZ_LAB = ZoneInfo("America/Sao_Paulo")

_log_file: Path | None = None
_dropped_logs: int = 0  # contador para warning único quando logger não inicializado/falha


def init_logger(app_dir: Path) -> None:
    global _log_file
    logs_dir = app_dir / "logs"
    logs_dir.mkdir(exist_ok=True)
    # Timestamp em segundos + sufixo aleatório curto: cada startup gera um nome
    # único, mesmo que dois startups ocorram no mesmo segundo (improvável mas
    # possível em container restart rápido). O sufixo garante que o log_viewer
    # sempre pegue o arquivo do startup atual, sem concatenar logs antigos.
    ts = datetime.now(tz=_TZ_LAB).strftime("%Y-%m-%d_%H-%M-%S")
    suffix = secrets.token_hex(2)  # 4 hex chars (~65k valores, suficiente)
    _log_file = logs_dir / f"{ts}_{suffix}.jsonl"
    _log_file.touch()


def new_request_id() -> str:
    return uuid.uuid4().hex[:8]


def log_entry(request_id: str, src: str, action: str, detail: str, elapsed_ms: float = 0.0) -> None:
    global _dropped_logs
    if _log_file is None:
        # FIX: avisar uma vez (não floodar) que logs estão sendo descartados.
        # Antes era silencioso — app rodava "no escuro" se init_logger falhasse.
        if _dropped_logs < 1:
            import sys
            print(f"[Logger] AVISO: init_logger() não foi chamado — logs descartados. "
                  f"src={src} action={action}", file=sys.stderr)
        _dropped_logs += 1
        return
    entry = {
        "ts": datetime.now(tz=_TZ_LAB).isoformat(),
        "request_id": request_id,
        "src": src,
        "action": action,
        "detail": detail,
        "elapsed_ms": round(elapsed_ms, 1),
    }
    try:
        with _log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as exc:
        # FIX: se disco cheio / permissão, loga uma vez e segue (não crashar app).
        if _dropped_logs < 1:
            import sys
            print(f"[Logger] AVISO: falha ao escrever log: {exc}", file=sys.stderr)
        _dropped_logs += 1
