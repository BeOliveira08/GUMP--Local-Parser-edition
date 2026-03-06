"""
GUMP/license.py
-----------------
Validação de licença — embutido no app.
Aceita: arquivo gump.license OU código de texto (license code).
NÃO contém lógica de geração de chaves.
"""

import hmac
import hashlib
import base64
import json
import uuid
import socket
import logging
from datetime import date
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Salt secreto ─────────────────────────────────────────────────────────────
# NUNCA altere após distribuir. NUNCA commite em repositório público.
_SECRET = b"G!u_mP#2026$xK9@wBc&nZqR3*vLtYeA"

LICENSE_FILE = Path(__file__).parent / "gump.license"


# ---------------------------------------------------------------------------
# Machine ID
# ---------------------------------------------------------------------------

def _get_machine_id() -> str:
    try:
        mac  = uuid.getnode()
        host = socket.gethostname()
        raw  = f"{mac}:{host}".encode()
        return hashlib.sha256(raw).hexdigest()[:32]
    except Exception:
        return "unknown_machine"


def get_machine_id_display() -> str:
    mid = _get_machine_id()
    return f"{mid[:8]}-{mid[8:16]}-{mid[16:24]}-{mid[24:32]}"


# ---------------------------------------------------------------------------
# Assinatura
# ---------------------------------------------------------------------------

def _compute_signature(payload: dict) -> str:
    canonical = json.dumps({
        "client":     payload["client"],
        "machine_id": payload["machine_id"],
        "expiry":     payload["expiry"],
        "issued":     payload["issued"],
    }, sort_keys=True, separators=(",", ":"))
    sig = hmac.new(_SECRET, canonical.encode(), hashlib.sha256).digest()
    return base64.b32encode(sig).decode()


# ---------------------------------------------------------------------------
# Encode / Decode do license code (texto compacto)
# ---------------------------------------------------------------------------

def encode_license_code(payload: dict) -> str:
    """Converte payload dict → string base64 compacta para enviar ao cliente."""
    compact = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    return base64.urlsafe_b64encode(compact.encode()).decode()


def decode_license_code(code: str) -> dict:
    """Converte license code (string) → payload dict."""
    raw = base64.urlsafe_b64decode(code.encode() + b"==")
    return json.loads(raw.decode())


# ---------------------------------------------------------------------------
# Resultado
# ---------------------------------------------------------------------------

class LicenseResult:
    def __init__(self, valid: bool, reason: str = "", client: str = "",
                 expiry: str = "", trial: bool = False):
        self.valid  = valid
        self.reason = reason
        self.client = client
        self.expiry = expiry
        self.trial  = trial

    def __bool__(self):
        return self.valid


# ---------------------------------------------------------------------------
# Validação do payload (comum a arquivo e código)
# ---------------------------------------------------------------------------

def _validate_payload(payload: dict) -> LicenseResult:
    for field in ("client", "machine_id", "expiry", "issued", "signature"):
        if field not in payload:
            return LicenseResult(False, reason="campos_faltando")

    expected = _compute_signature(payload)
    if not hmac.compare_digest(expected, payload["signature"]):
        return LicenseResult(False, reason="assinatura_invalida")

    current_machine = _get_machine_id()
    if payload["machine_id"] != "ANY" and payload["machine_id"] != current_machine:
        return LicenseResult(False, reason="maquina_diferente")

    if payload["expiry"] != "NEVER":
        try:
            expiry_date = date.fromisoformat(payload["expiry"])
            if date.today() > expiry_date:
                return LicenseResult(False, reason="expirada",
                                     client=payload["client"], expiry=payload["expiry"])
        except ValueError:
            return LicenseResult(False, reason="data_invalida")

    return LicenseResult(
        valid=True,
        client=payload["client"],
        expiry=payload["expiry"],
        trial=payload.get("trial", False),
    )


# ---------------------------------------------------------------------------
# Validação — arquivo
# ---------------------------------------------------------------------------

def validate_license_file(license_path: Path = None) -> LicenseResult:
    path = license_path or LICENSE_FILE
    if not path.exists():
        return LicenseResult(False, reason="arquivo_nao_encontrado")
    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except Exception:
        return LicenseResult(False, reason="arquivo_corrompido")
    return _validate_payload(payload)


# ---------------------------------------------------------------------------
# Validação — código de texto
# ---------------------------------------------------------------------------

def validate_license_code(code: str) -> LicenseResult:
    code = code.strip()
    if not code:
        return LicenseResult(False, reason="codigo_vazio")
    try:
        payload = decode_license_code(code)
    except Exception:
        return LicenseResult(False, reason="codigo_invalido")
    return _validate_payload(payload)


def save_license_from_code(code: str, path: Path = None) -> bool:
    """Salva o gump.license a partir de um license code válido."""
    try:
        payload = decode_license_code(code.strip())
        out = path or LICENSE_FILE
        with open(out, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Validação principal — tenta arquivo, depois código
# ---------------------------------------------------------------------------

def validate_license(license_path: Path = None) -> LicenseResult:
    """Tenta validar via arquivo. Se não existir, retorna arquivo_nao_encontrado."""
    return validate_license_file(license_path)


# ---------------------------------------------------------------------------
# Utils
# ---------------------------------------------------------------------------

def days_until_expiry(expiry: str):
    if expiry == "NEVER":
        return None
    try:
        return (date.fromisoformat(expiry) - date.today()).days
    except ValueError:
        return 0
