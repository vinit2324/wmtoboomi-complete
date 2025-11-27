import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
if not MONGODB_URL:
    print("❌ Error: MONGODB_URL not set in .env")
    exit(1)

async def cleanup():
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client.wmtoboomi
    
    # Delete all projects
    result = await db.projects.delete_many({})
    print(f"Deleted {result.deleted_count} old projects")
    print("\nNow restart backend and re-upload the package!")

asyncio.run(cleanup())
