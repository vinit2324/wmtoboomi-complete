"""
Database configuration - Secure version using environment variables.
"""
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME", "wmtoboomi")

if not MONGODB_URL:
    raise ValueError(
        "❌ MONGODB_URL environment variable is required!\n"
        "Please create a .env file with your MongoDB connection string."
    )

client = AsyncIOMotorClient(MONGODB_URL)
db = client[DATABASE_NAME]


async def connect_to_mongodb():
    try:
        await client.admin.command('ping')
        print(f"✅ MongoDB connected to database: {DATABASE_NAME}")
        return True
    except Exception as e:
        print(f"❌ MongoDB connection error: {e}")
        return False


async def disconnect_from_mongodb():
    client.close()
    print("MongoDB connection closed")


async def check_database_health():
    try:
        await client.admin.command('ping')
        return {"status": "healthy", "connected": True, "database": DATABASE_NAME}
    except Exception as e:
        return {"status": "unhealthy", "connected": False, "database": DATABASE_NAME, "error": str(e)}
