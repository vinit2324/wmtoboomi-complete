"""AI Assistant - Real LLM Integration with Fixed Data Reading"""
from fastapi import APIRouter
from app.database import db
from datetime import datetime
import httpx
import os

router = APIRouter(prefix="/api/ai", tags=["ai"])


async def get_llm_config():
    """Get LLM configuration from customer or env"""
    
    customer = await db.customers.find_one({})
    if customer and customer.get('settings', {}).get('llm'):
        llm = customer['settings']['llm']
        return {
            'provider': llm.get('provider', 'openai'),
            'api_key': llm.get('apiKey', ''),
            'model': llm.get('model', 'gpt-4'),
        }
    
    return {
        'provider': os.getenv('LLM_PROVIDER', 'openai'),
        'api_key': os.getenv('OPENAI_API_KEY', os.getenv('ANTHROPIC_API_KEY', '')),
        'model': os.getenv('LLM_MODEL', 'gpt-4'),
    }


async def build_context() -> str:
    """Build rich context from all projects - FIXED DATA READING"""
    
    context_parts = []
    
    projects = []
    async for project in db.projects.find().sort("uploadedAt", -1):
        projects.append(project)
    
    if not projects:
        return "No webMethods packages have been uploaded yet."
    
    context_parts.append(f"=== UPLOADED PACKAGES ({len(projects)}) ===\n")
    
    for project in projects:
        pkg_name = project.get('packageName', 'Unknown')
        status = project.get('status', 'unknown')
        uploaded = project.get('uploadedAt', '')
        
        # Get parsed data - check multiple possible locations
        parsed_data = project.get('parsedData', {})
        
        # Services can be in different places
        services = parsed_data.get('services', [])
        if not services:
            services = project.get('services', [])
        
        # Documents can be in different places
        documents = parsed_data.get('documents', [])
        if not documents:
            documents = project.get('documents', [])
        
        # Package info might have summary stats
        pkg_info = project.get('packageInfo', {})
        svc_info = pkg_info.get('services', {})
        
        # Count by type from actual services
        flow_services = [s for s in services if s.get('type') == 'FlowService']
        java_services = [s for s in services if s.get('type') == 'JavaService']
        adapter_services = [s for s in services if s.get('type') == 'AdapterService']
        
        # If no services found in array, try to get counts from packageInfo
        total_svc = len(services) or svc_info.get('total', 0)
        flow_count = len(flow_services) or svc_info.get('flow', 0)
        java_count = len(java_services) or svc_info.get('java', 0)
        adapter_count = len(adapter_services) or svc_info.get('adapter', 0)
        doc_count = len(documents) or svc_info.get('document', 0)
        
        # Count flow verbs
        verb_counts = {'MAP': 0, 'BRANCH': 0, 'LOOP': 0, 'INVOKE': 0, 'SEQUENCE': 0}
        for svc in flow_services:
            flow_steps = svc.get('flowSteps', [])
            for step in flow_steps:
                t = step.get('type', '')
                if t in verb_counts:
                    verb_counts[t] += 1
        
        # Also check flowVerbStats in packageInfo
        verb_stats = pkg_info.get('flowVerbStats', {})
        if verb_stats:
            for v in verb_counts:
                verb_counts[v] = verb_counts[v] or verb_stats.get(v.lower(), 0)
        
        pkg_context = f"""
========================================
PACKAGE: {pkg_name}
========================================
Status: {status}
Uploaded: {uploaded}

SERVICES SUMMARY:
- Total Services: {total_svc}
- Flow Services: {flow_count}
- Java Services: {java_count}
- Adapter Services: {adapter_count}
- Document Types: {doc_count}

FLOW VERB COUNTS:
- MAP: {verb_counts['MAP']}
- BRANCH: {verb_counts['BRANCH']}
- LOOP: {verb_counts['LOOP']}
- INVOKE: {verb_counts['INVOKE']}
- SEQUENCE: {verb_counts['SEQUENCE']}
"""
        
        # Add service names if available
        if flow_services:
            pkg_context += "\nFLOW SERVICES:\n"
            for svc in flow_services[:15]:
                name = svc.get('name', 'Unknown')
                steps = len(svc.get('flowSteps', []))
                pkg_context += f"  - {name} ({steps} steps)\n"
            if len(flow_services) > 15:
                pkg_context += f"  ... and {len(flow_services) - 15} more\n"
        
        if documents:
            pkg_context += "\nDOCUMENT TYPES:\n"
            for doc in documents[:10]:
                name = doc.get('name', 'Unknown')
                fields = len(doc.get('fields', []))
                pkg_context += f"  - {name} ({fields} fields)\n"
        
        context_parts.append(pkg_context)
    
    return "\n".join(context_parts)


def get_system_prompt() -> str:
    """System prompt for migration assistant"""
    
    return """You are an expert AI Migration Assistant for the webMethods to Boomi Migration Accelerator platform by Jade Global Inc.

YOUR EXPERTISE:
- Software AG webMethods integration platform
- Boomi iPaaS platform
- Migrating integrations from webMethods to Boomi
- The 9 webMethods flow verbs: MAP, BRANCH, LOOP, REPEAT, SEQUENCE, Try/Catch, Try/Finally, Catch, Finally, Exit
- wMPublic services (pub.string, pub.flow, pub.math, etc.)
- Pipeline/heap structure in webMethods
- Boomi shapes, connectors, profiles, and processes

WEBMETHODS TO BOOMI MAPPINGS:
- Flow Service → Boomi Process
- Document Type → Boomi Profile (XML/JSON/EDI/Flat)
- MAP verb → Map Shape or Set Properties
- BRANCH verb → Decision Shape
- LOOP verb → ForEach Shape (often implicit in Boomi)
- SEQUENCE → Try/Catch Shape
- INVOKE → Connector Shape or Process Call
- Java Service → Data Process with Groovy (requires manual conversion)
- JDBC Adapter → Database Connector
- HTTP Adapter → HTTP Client Connector

AUTOMATION LEVELS:
- Flow Services (simple): 90% automatable
- Flow Services (complex): 70% automatable
- Document Types: 95% automatable
- Adapters: 50-80% automatable
- Java Services: 20% automatable (manual Groovy conversion)
- Overall target: 80-90% automation

YOUR ROLE:
1. Answer questions about uploaded webMethods packages using the context provided
2. Provide migration guidance and best practices
3. Explain conversion mappings between webMethods and Boomi
4. Estimate effort and complexity
5. Be helpful, accurate, and actionable

Use the ACTUAL DATA from the context. Give specific numbers and details from real uploaded packages.
Format responses with markdown for readability.
"""


async def call_openai(api_key: str, model: str, messages: list) -> str:
    """Call OpenAI API"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": model, "messages": messages, "temperature": 0.7, "max_tokens": 2000}
        )
        if response.status_code != 200:
            raise Exception(f"OpenAI error: {response.status_code} - {response.text}")
        return response.json()['choices'][0]['message']['content']


async def call_anthropic(api_key: str, model: str, messages: list) -> str:
    """Call Anthropic API"""
    system = ""
    user_messages = []
    for msg in messages:
        if msg['role'] == 'system':
            system = msg['content']
        else:
            user_messages.append(msg)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"},
            json={"model": model or "claude-3-sonnet-20240229", "max_tokens": 2000, "system": system, "messages": user_messages}
        )
        if response.status_code != 200:
            raise Exception(f"Anthropic error: {response.status_code} - {response.text}")
        return response.json()['content'][0]['text']


async def call_llm(config: dict, messages: list) -> str:
    """Call configured LLM"""
    provider = config['provider'].lower()
    api_key = config['api_key']
    model = config['model']
    
    if not api_key:
        raise Exception("No API key configured")
    
    if provider in ['openai', 'gpt']:
        return await call_openai(api_key, model or 'gpt-4', messages)
    elif provider in ['anthropic', 'claude']:
        return await call_anthropic(api_key, model, messages)
    else:
        raise Exception(f"Unsupported provider: {provider}")


@router.post("/chat")
async def chat(data: dict):
    """AI Chat endpoint"""
    
    message = data.get("message", "").strip()
    project_id = data.get("projectId")
    history = data.get("history", [])
    
    if not message:
        return {"response": "Please enter a question!"}
    
    try:
        config = await get_llm_config()
        context = await build_context()
        
        messages = [
            {"role": "system", "content": get_system_prompt() + f"\n\n=== CURRENT PROJECT DATA ===\n{context}"}
        ]
        
        for h in history[-10:]:
            messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
        
        messages.append({"role": "user", "content": message})
        
        response = await call_llm(config, messages)
        
        try:
            await db.logs.insert_one({
                "timestamp": datetime.utcnow(),
                "level": "info",
                "category": "ai",
                "action": "chat",
                "message": f"AI: {message[:100]}",
                "metadata": {"projectId": project_id, "provider": config['provider']}
            })
        except:
            pass
        
        return {"response": response}
    
    except Exception as e:
        # Fallback to local response with actual context
        context = await build_context()
        return {
            "response": f"""**⚠️ LLM Connection Issue**

{str(e)}

**To configure LLM:** Go to Customers → Edit → Add LLM settings (OpenAI/Claude API key)

---

**📊 Here's what I found in your packages:**

{context}

---

**Need help?** Try these questions after configuring LLM:
- "Analyze the complexity of this package"
- "How do I convert LOOP to Boomi?"
- "Estimate migration effort"
"""
        }


@router.get("/debug-data")
async def debug_data():
    """Debug endpoint to see actual data structure"""
    
    projects = []
    async for project in db.projects.find().limit(1):
        # Return first project structure for debugging
        projects.append({
            "projectId": project.get("projectId"),
            "packageName": project.get("packageName"),
            "status": project.get("status"),
            "keys": list(project.keys()),
            "parsedData_keys": list(project.get("parsedData", {}).keys()) if project.get("parsedData") else [],
            "packageInfo": project.get("packageInfo", {}),
            "services_count": len(project.get("parsedData", {}).get("services", [])),
            "sample_service": project.get("parsedData", {}).get("services", [{}])[0] if project.get("parsedData", {}).get("services") else None
        })
    
    return {"projects": projects}
