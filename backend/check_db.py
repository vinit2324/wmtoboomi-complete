import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check():
    client = AsyncIOMotorClient("mongodb+srv://vinit:Delhi123@vvmdb1.6umwxkw.mongodb.net/wmtoboomi?retryWrites=true&w=majority&appName=VVMDB1")
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
