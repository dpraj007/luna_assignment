import asyncio
import sys
import os

# Add the backend directory to the path (where this script is located)
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from app.core.database import get_db, engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.user import Friendship

async def check_friendships():
    async with AsyncSession(engine) as db:
        # Count total friendships
        count_query = select(func.count()).select_from(Friendship)
        result = await db.execute(count_query)
        total = result.scalar()
        print(f"Total friendships in database: {total}")
        
        # Count friendships for user 1
        count_query_user1 = select(func.count()).select_from(Friendship).where(Friendship.user_id == 1)
        result = await db.execute(count_query_user1)
        user1_count = result.scalar()
        print(f"Friendships for user 1: {user1_count}")
        
        # Get all friendships for user 1
        query = select(Friendship).where(Friendship.user_id == 1)
        result = await db.execute(query)
        friendships = result.scalars().all()
        print(f"Friend IDs for user 1: {[f.friend_id for f in friendships]}")

if __name__ == "__main__":
    asyncio.run(check_friendships())

