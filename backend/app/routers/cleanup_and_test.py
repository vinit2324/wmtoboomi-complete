import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def cleanup():
    client = AsyncIOMotorClient("mongodb+srv://vinit:Delhi123@vvmdb1.6umwxkw.mongodb.net/wmtoboomi?retryWrites=true&w=majority&appName=VVMDB1")
    db = client.wmtoboomi
    
    # Delete all projects
    result = await db.projects.delete_many({})
    print(f"✅ Deleted {result.deleted_count} old projects")
    print("\nNow restart backend and re-upload the package!")

asyncio.run(cleanup())
