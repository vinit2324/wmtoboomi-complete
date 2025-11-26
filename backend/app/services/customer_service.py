"""
Customer service for multi-customer management.
"""
import uuid
from datetime import datetime
from typing import Optional
import httpx
from bson import ObjectId

from app.database import get_customers_collection
from app.config import EncryptionService
from app.models import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerListResponse,
    CustomerSettings,
    BoomiSettings,
    LLMSettings,
    ConnectionTestResult,
)
from app.services.logging_service import log_activity


class CustomerService:
    """Service for managing customers."""
    
    @staticmethod
    def _encrypt_settings(settings: CustomerSettings) -> dict:
        """Encrypt sensitive fields in settings."""
        settings_dict = settings.model_dump()
        
        # Encrypt Boomi API token
        if settings_dict["boomi"]["apiToken"]:
            settings_dict["boomi"]["apiToken"] = EncryptionService.encrypt(
                settings_dict["boomi"]["apiToken"]
            )
        
        # Encrypt LLM API key
        if settings_dict["llm"]["apiKey"]:
            settings_dict["llm"]["apiKey"] = EncryptionService.encrypt(
                settings_dict["llm"]["apiKey"]
            )
        
        return settings_dict
    
    @staticmethod
    def _decrypt_settings(settings_dict: dict) -> CustomerSettings:
        """Decrypt sensitive fields in settings."""
        # Decrypt Boomi API token
        if settings_dict.get("boomi", {}).get("apiToken"):
            try:
                settings_dict["boomi"]["apiToken"] = EncryptionService.decrypt(
                    settings_dict["boomi"]["apiToken"]
                )
            except Exception:
                settings_dict["boomi"]["apiToken"] = ""
        
        # Decrypt LLM API key
        if settings_dict.get("llm", {}).get("apiKey"):
            try:
                settings_dict["llm"]["apiKey"] = EncryptionService.decrypt(
                    settings_dict["llm"]["apiKey"]
                )
            except Exception:
                settings_dict["llm"]["apiKey"] = ""
        
        return CustomerSettings(**settings_dict)
    
    @staticmethod
    async def create(data: CustomerCreate) -> CustomerResponse:
        """Create a new customer."""
        customers = get_customers_collection()
        
        customer_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        settings = data.settings or CustomerSettings()
        encrypted_settings = CustomerService._encrypt_settings(settings)
        
        doc = {
            "customerId": customer_id,
            "customerName": data.customerName,
            "createdAt": now,
            "updatedAt": now,
            "settings": encrypted_settings,
            "isActive": True
        }
        
        await customers.insert_one(doc)
        
        await log_activity(
            action="customer_created",
            message=f"Customer '{data.customerName}' created",
            category="system",
            customer_id=customer_id
        )
        
        return CustomerResponse(
            customerId=customer_id,
            customerName=data.customerName,
            createdAt=now,
            updatedAt=now,
            settings=settings,
            isActive=True
        )
    
    @staticmethod
    async def get(customer_id: str) -> Optional[CustomerResponse]:
        """Get a customer by ID."""
        customers = get_customers_collection()
        
        doc = await customers.find_one({"customerId": customer_id})
        if not doc:
            return None
        
        settings = CustomerService._decrypt_settings(doc.get("settings", {}))
        
        return CustomerResponse(
            customerId=doc["customerId"],
            customerName=doc["customerName"],
            createdAt=doc["createdAt"],
            updatedAt=doc["updatedAt"],
            settings=settings,
            isActive=doc.get("isActive", True)
        )
    
    @staticmethod
    async def list_all() -> CustomerListResponse:
        """List all customers."""
        customers = get_customers_collection()
        
        cursor = customers.find({"isActive": True}).sort("customerName", 1)
        
        customer_list = []
        async for doc in cursor:
            settings = CustomerService._decrypt_settings(doc.get("settings", {}))
            customer_list.append(CustomerResponse(
                customerId=doc["customerId"],
                customerName=doc["customerName"],
                createdAt=doc["createdAt"],
                updatedAt=doc["updatedAt"],
                settings=settings,
                isActive=doc.get("isActive", True)
            ))
        
        return CustomerListResponse(
            customers=customer_list,
            total=len(customer_list)
        )
    
    @staticmethod
    async def update(customer_id: str, data: CustomerUpdate) -> Optional[CustomerResponse]:
        """Update a customer."""
        customers = get_customers_collection()
        
        update_doc = {"updatedAt": datetime.utcnow()}
        
        if data.customerName is not None:
            update_doc["customerName"] = data.customerName
        
        if data.settings is not None:
            update_doc["settings"] = CustomerService._encrypt_settings(data.settings)
        
        result = await customers.update_one(
            {"customerId": customer_id},
            {"$set": update_doc}
        )
        
        if result.matched_count == 0:
            return None
        
        await log_activity(
            action="customer_updated",
            message=f"Customer updated",
            category="system",
            customer_id=customer_id
        )
        
        return await CustomerService.get(customer_id)
    
    @staticmethod
    async def delete(customer_id: str) -> bool:
        """Soft delete a customer."""
        customers = get_customers_collection()
        
        result = await customers.update_one(
            {"customerId": customer_id},
            {"$set": {"isActive": False, "updatedAt": datetime.utcnow()}}
        )
        
        if result.matched_count > 0:
            await log_activity(
                action="customer_deleted",
                message=f"Customer deleted",
                category="system",
                customer_id=customer_id
            )
            return True
        
        return False
    
    @staticmethod
    async def test_boomi_connection(customer_id: str) -> ConnectionTestResult:
        """Test Boomi API connection for a customer."""
        customer = await CustomerService.get(customer_id)
        if not customer:
            return ConnectionTestResult(
                success=False,
                message="Customer not found"
            )
        
        boomi = customer.settings.boomi
        if not boomi.accountId or not boomi.username or not boomi.apiToken:
            return ConnectionTestResult(
                success=False,
                message="Boomi credentials not configured"
            )
        
        try:
            import base64
            auth_string = f"BOOMI_TOKEN.{boomi.username}:{boomi.apiToken}"
            auth_header = base64.b64encode(auth_string.encode()).decode()
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{boomi.baseUrl}/{boomi.accountId}/Account/{boomi.accountId}",
                    headers={
                        "Authorization": f"Basic {auth_header}",
                        "Accept": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    return ConnectionTestResult(
                        success=True,
                        message="Successfully connected to Boomi API",
                        details={"accountId": boomi.accountId}
                    )
                else:
                    return ConnectionTestResult(
                        success=False,
                        message=f"Boomi API returned status {response.status_code}",
                        details={"response": response.text[:200]}
                    )
        
        except httpx.TimeoutException:
            return ConnectionTestResult(
                success=False,
                message="Connection timed out"
            )
        except Exception as e:
            return ConnectionTestResult(
                success=False,
                message=f"Connection failed: {str(e)}"
            )
    
    @staticmethod
    async def test_llm_connection(customer_id: str) -> ConnectionTestResult:
        """Test LLM API connection for a customer."""
        customer = await CustomerService.get(customer_id)
        if not customer:
            return ConnectionTestResult(
                success=False,
                message="Customer not found"
            )
        
        llm = customer.settings.llm
        if not llm.apiKey and llm.provider != "ollama":
            return ConnectionTestResult(
                success=False,
                message="LLM API key not configured"
            )
        
        try:
            if llm.provider == "openai":
                import openai
                client = openai.AsyncOpenAI(api_key=llm.apiKey)
                models = await client.models.list()
                return ConnectionTestResult(
                    success=True,
                    message="Successfully connected to OpenAI API",
                    details={"models_count": len(list(models))}
                )
            
            elif llm.provider == "anthropic":
                import anthropic
                client = anthropic.AsyncAnthropic(api_key=llm.apiKey)
                # Test with a minimal request
                response = await client.messages.create(
                    model=llm.model or "claude-3-sonnet-20240229",
                    max_tokens=10,
                    messages=[{"role": "user", "content": "Hi"}]
                )
                return ConnectionTestResult(
                    success=True,
                    message="Successfully connected to Anthropic API"
                )
            
            elif llm.provider == "gemini":
                import google.generativeai as genai
                genai.configure(api_key=llm.apiKey)
                models = genai.list_models()
                return ConnectionTestResult(
                    success=True,
                    message="Successfully connected to Google Gemini API"
                )
            
            elif llm.provider == "ollama":
                async with httpx.AsyncClient(timeout=10.0) as client:
                    base_url = llm.baseUrl or "http://localhost:11434"
                    response = await client.get(f"{base_url}/api/tags")
                    if response.status_code == 200:
                        return ConnectionTestResult(
                            success=True,
                            message="Successfully connected to Ollama",
                            details=response.json()
                        )
                    else:
                        return ConnectionTestResult(
                            success=False,
                            message=f"Ollama returned status {response.status_code}"
                        )
            
            else:
                return ConnectionTestResult(
                    success=False,
                    message=f"Unknown LLM provider: {llm.provider}"
                )
        
        except Exception as e:
            return ConnectionTestResult(
                success=False,
                message=f"Connection failed: {str(e)}"
            )
