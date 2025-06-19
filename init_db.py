# init_db.py
import asyncio

from backend.db import engine, Base
import backend.models.user
import backend.models.call_session
import backend.models.participant
import backend.models.signaling
import backend.models.message

async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    print("🗄️  Creating tables…")
    asyncio.run(init_models())
    print("✅  Done.")
