import asyncio
from sqlalchemy import select, and_
from app.core.database import get_db
from app.models.review import Review, ReviewStatus

async def test_query():
    async for db in get_db():
        # Test with string
        query1 = select(Review).where(
            and_(
                Review.reviewer_id == "ff54961a-63ac-4fda-8e9e-986209e3e6a5",
                Review.status == "pending"
            )
        )
        print("Query 1 (string):", query1)
        
        # Test with enum
        query2 = select(Review).where(
            and_(
                Review.reviewer_id == "ff54961a-63ac-4fda-8e9e-986209e3e6a5",
                Review.status == ReviewStatus.PENDING
            )
        )
        print("Query 2 (enum):", query2)
        
        # Execute query 1
        try:
            result1 = await db.execute(query1)
            print("Query 1 executed successfully")
        except Exception as e:
            print(f"Query 1 failed: {e}")
        
        # Execute query 2
        try:
            result2 = await db.execute(query2)
            print("Query 2 executed successfully")
        except Exception as e:
            print(f"Query 2 failed: {e}")
        
        break

if __name__ == "__main__":
    asyncio.run(test_query())
