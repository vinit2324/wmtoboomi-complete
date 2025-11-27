import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
if not MONGODB_URL:
    print("❌ Error: MONGODB_URL not set in .env")
    exit(1)

async def check():
    client = AsyncIOMotorClient(MONGODB_URL)
    db = client.wmtoboomi
    
    print("=== PROJECTS IN DATABASE ===\n")
    
    async for project in db.projects.find().limit(2):
        print(f"Package: {project.get('packageName')}")
        print(f"Status: {project.get('status')}")
        print(f"Keys: {list(project.keys())}")
        
        parsed = project.get('parsedData', {})
        print(f"parsedData keys: {list(parsed.keys()) if parsed else 'EMPTY'}")
        
        services = parsed.get('services', [])
        print(f"Services count: {len(services)}")
        
        if services:
            print(f"First service: {services[0]}")
        
        pkg_info = project.get('packageInfo', {})
        print(f"packageInfo: {pkg_info}")
        
        print("\n" + "="*50 + "\n")

asyncio.run(check())
