from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import jwt


def create_access_token(
    data: Dict[str, Any],
    secret_key: str,
    expires_delta: timedelta | None = None,
) -> str:
    to_encode = data.copy()
    if expires_delta is None:
        expires_delta = timedelta(hours=8)
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm="HS256")
    return encoded_jwt


def decode_access_token(token: str, secret_key: str) -> Dict[str, Any] | None:
    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        return payload
    except jwt.PyJWTError:
        return None


