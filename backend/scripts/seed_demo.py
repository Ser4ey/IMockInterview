import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db.session import AsyncSessionLocal
from app.db.session import engine
from app.db.schema_sync import prepare_database
from app.services.demo_seed import seed_demo_data


async def main() -> None:
    await prepare_database(engine)

    async with AsyncSessionLocal() as db:
        result = await seed_demo_data(db)
    print(
        "Demo data is ready: "
        f"admin={result['admin_email']} / {result['admin_password']}, "
        f"user={result['user_email']} / {result['user_password']}, "
        f"interview_id={result['interview_id']}"
    )


if __name__ == "__main__":
    asyncio.run(main())
