import bcrypt

# passlib 1.7.4 is incompatible with bcrypt 5.x (missing __about__ attribute).
# Using bcrypt directly is cleaner and avoids the version mismatch entirely.

def hash_password(plain_password: str) -> str:
    """
    Hash a plain-text password using bcrypt.
    bcrypt has a hard limit of 72 bytes — passwords longer than that are silently truncated.
    We enforce this limit explicitly to avoid silent data loss.
    """
    encoded = plain_password.encode("utf-8")
    if len(encoded) > 72:
        raise ValueError(
            f"Password is {len(encoded)} bytes — bcrypt only processes the first 72. "
            "Please shorten your SUPER_ADMIN_SEED_PASSWORD in .env."
        )
    return bcrypt.hashpw(encoded, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a stored bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )
