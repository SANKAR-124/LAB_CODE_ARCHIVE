"""
Stage 4 — Super admin seed script.
Run once from the backend/ directory:
    python -m app.scripts.seed_super_admin

It reads credentials from .env via settings, hashes the password,
and inserts one super_admin row into users.
Running it a second time is safe — it skips if the username already exists.
"""

from app.db.session import Sessionlocal
from app.models.user import users
from app.core.config import settings
from app.core.security import hash_password


def seed() -> None:
    db = Sessionlocal()
    try:
        # Guard: skip if a user with this username already exists
        existing = db.query(users).filter(users.username == settings.SUPER_ADMIN_SEED_USERNAME).first()
        if existing:
            print(f"[SKIP] Super admin '{settings.SUPER_ADMIN_SEED_USERNAME}' already exists. Nothing inserted.")
            return

        super_admin = users(
            username=settings.SUPER_ADMIN_SEED_USERNAME,
            email=settings.SUPER_ADMIN_SEED_EMAIL,
            password_hash=hash_password(settings.SUPER_ADMIN_SEED_PASSWORD),
            role="super_admin",
        )

        db.add(super_admin)
        db.commit()
        print(f"[OK] Super admin '{settings.SUPER_ADMIN_SEED_USERNAME}' created successfully.")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] Seeding failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
