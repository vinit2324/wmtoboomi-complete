"""
MongoDB database connection and management using Motor (async driver).
"""
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure

from app.config import get_settings


class Database:
    """MongoDB database connection manager."""
    
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None
    
    @classmethod
    async def connect(cls) -> None:
        """Establish connection to MongoDB."""
        settings = get_settings()
        
        try:
            cls.client = AsyncIOMotorClient(
                settings.mongodb_url,
                serverSelectionTimeoutMS=5000,
                maxPoolSize=50,
                minPoolSize=10
            )
            
            # Verify connection
            await cls.client.admin.command('ping')
            
            cls.db = cls.client[settings.database_name]
            
            # Create indexes
            await cls._create_indexes()
            
            print(f"✅ Connected to MongoDB: {settings.database_name}")
            
        except ConnectionFailure as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            raise
    
    @classmethod
    async def disconnect(cls) -> None:
        """Close MongoDB connection."""
        if cls.client:
            cls.client.close()
            cls.client = None
            cls.db = None
            print("📤 Disconnected from MongoDB")
    
    @classmethod
    async def _create_indexes(cls) -> None:
        """Create database indexes for optimal performance."""
        if cls.db is None:
            return
        
        # Customers collection indexes
        await cls.db.customers.create_index("customerId", unique=True)
        await cls.db.customers.create_index("customerName")
        
        # Projects collection indexes
        await cls.db.projects.create_index("projectId", unique=True)
        await cls.db.projects.create_index("customerId")
        await cls.db.projects.create_index("status")
        await cls.db.projects.create_index([("uploadedAt", -1)])
        
        # Conversions collection indexes
        await cls.db.conversions.create_index("conversionId", unique=True)
        await cls.db.conversions.create_index("projectId")
        await cls.db.conversions.create_index("customerId")
        await cls.db.conversions.create_index("status")
        
        # Mappings collection indexes
        await cls.db.mappings.create_index("mappingId", unique=True)
        await cls.db.mappings.create_index("projectId")
        
        # Logs collection indexes
        await cls.db.logs.create_index([("timestamp", -1)])
        await cls.db.logs.create_index("customerId")
        await cls.db.logs.create_index("projectId")
        await cls.db.logs.create_index("category")
        await cls.db.logs.create_index("level")
        
        print("📇 Database indexes created/verified")
    
    @classmethod
    def get_collection(cls, name: str):
        """Get a collection by name."""
        if cls.db is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return cls.db[name]


# Collection shortcuts
def get_customers_collection():
    return Database.get_collection("customers")

def get_projects_collection():
    return Database.get_collection("projects")

def get_conversions_collection():
    return Database.get_collection("conversions")

def get_mappings_collection():
    return Database.get_collection("mappings")

def get_logs_collection():
    return Database.get_collection("logs")
