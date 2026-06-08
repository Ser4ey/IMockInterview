import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User

logger = logging.getLogger(__name__)


async def ensure_admin_user(db: AsyncSession) -> User | None:
    email = settings.ADMIN_EMAIL.strip().lower()
    password = settings.ADMIN_PASSWORD
    full_name = settings.ADMIN_FULL_NAME.strip() or "Администратор IMock"

    if not email or not password:
        logger.info("Production admin bootstrap skipped: ADMIN_EMAIL or ADMIN_PASSWORD is empty")
        return None

    user = await db.scalar(select(User).where(User.email == email))
    if not user:
        user = User(email=email)
        db.add(user)

    user.hashed_password = get_password_hash(password)
    user.full_name = full_name
    user.role = "admin"
    user.is_superuser = True
    user.is_active = True

    await db.commit()
    await db.refresh(user)
    logger.info("Production admin user is ready: %s", email)
    return user
