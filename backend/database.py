"""Database configuration"""
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv(
    "MONGODB_URL",
    "mongodb+srv://vinit:Delhi123@vvmdb1.6umwxkw.mongodb.net/wmtoboomi?retryWrites=true&w=majority&appName=VVMDB1"
)
DATABASE_NAME = "wmtoboomi"

client = AsyncIOMotorClient(MONGODB_URL)
db = client[DATABASE_NAME]

async def connect_to_mongodb():
    try:
        await client.admin.command('ping')
        print("✅ MongoDB connected")
        return True
    except Exception as e:
        print(f"❌ MongoDB error: {e}")
        return False

async def disconnect_from_mongodb():
    client.close()

async def check_database_health():
    try:
        await client.admin.command('ping')
        return {"status": "healthy", "connected": True, "database": DATABASE_NAME}
    except:
        return {"status": "unhealthy", "connected": False, "database": DATABASE_NAME}
