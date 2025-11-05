# auth.py
import os
import time
import bcrypt
import jwt
from typing import Optional

# Hinweis: Für Produktion setzen wir JWT_SECRET später in Render als Environment Variable.
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")  # TODO: in Render setzen
JWT_ALG = "HS256"
JWT_TTL_SECONDS = 7 * 24 * 3600  # 7 Tage

def hash_pw(pw: str) -> str:
    """Erstellt einen sicheren Hash für das Passwort (bcrypt)."""
    return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def check_pw(pw: str, h: str) -> bool:
    """Vergleicht Klartext-Passwort mit gespeichertem Hash."""
    try:
        return bcrypt.checkpw(pw.encode("utf-8"), h.encode("utf-8"))
    except Exception:
        return False

def make_jwt(user_id: str) -> str:
    """Erzeugt ein kurzlebiges JWT für den eingeloggten User."""
    now = int(time.time())
    payload = {"sub": user_id, "iat": now, "exp": now + JWT_TTL_SECONDS}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def parse_jwt(token: str) -> Optional[str]:
    """Liest ein JWT und gibt die User-ID (sub) zurück, oder None bei Fehler."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
        return payload.get("sub")
    except Exception:
        return None
