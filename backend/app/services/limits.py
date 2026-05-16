from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.interview import TariffLimit
from app.models.user import User


class LimitExceededError(Exception):
    pass


@dataclass(frozen=True)
class LimitStatus:
    daily_limit: int
    used_today: int
    remaining_today: int
    reset_at: datetime


class LimitService:
    async def get_status(self, db: AsyncSession, user: User) -> LimitStatus:
        limit = await self._get_or_create_limit(db, user)
        self._reset_if_needed(limit)
        return self._to_status(limit)

    async def consume_interview_message(self, db: AsyncSession, user: User) -> LimitStatus:
        limit = await self._get_or_create_limit(db, user)
        self._reset_if_needed(limit)
        if limit.used_today >= limit.daily_limit:
            raise LimitExceededError("Дневной лимит сообщений интервью исчерпан")

        limit.used_today += 1
        user.requests_count = (user.requests_count or 0) + 1
        db.add(limit)
        db.add(user)
        return self._to_status(limit)

    async def _get_or_create_limit(self, db: AsyncSession, user: User) -> TariffLimit:
        result = await db.execute(select(TariffLimit).where(TariffLimit.user_id == user.id))
        limit = result.scalars().first()
        if limit:
            return limit

        limit = TariffLimit(
            user_id=user.id,
            daily_limit=self._default_limit_for_user(user),
            used_today=0,
            reset_at=self._next_reset_at(),
        )
        db.add(limit)
        await db.flush()
        return limit

    def _default_limit_for_user(self, user: User) -> int:
        if user.tariff == "pro":
            return 100
        return 20

    def _reset_if_needed(self, limit: TariffLimit) -> None:
        now = datetime.now(timezone.utc)
        reset_at = self._as_aware_datetime(limit.reset_at) if limit.reset_at else None
        if reset_at is None:
            limit.reset_at = self._next_reset_at(now)
            return

        if reset_at <= now:
            limit.used_today = 0
            limit.reset_at = self._next_reset_at(now)

    def _to_status(self, limit: TariffLimit) -> LimitStatus:
        reset_at = self._as_aware_datetime(limit.reset_at) if limit.reset_at else self._next_reset_at()
        remaining = max(limit.daily_limit - limit.used_today, 0)
        return LimitStatus(
            daily_limit=limit.daily_limit,
            used_today=limit.used_today,
            remaining_today=remaining,
            reset_at=reset_at,
        )

    def _next_reset_at(self, now: datetime | None = None) -> datetime:
        current = now or datetime.now(timezone.utc)
        return current + timedelta(days=1)

    def _as_aware_datetime(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value


limit_service = LimitService()
