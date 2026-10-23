from __future__ import annotations

import bcrypt

# bcrypt hashes at most 72 bytes; longer input raises in bcrypt >= 4, so schemas cap passwords at 72.


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
