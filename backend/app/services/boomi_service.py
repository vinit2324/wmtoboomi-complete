"""
Boomi API service for pushing components to Boomi Platform.
"""
import base64
import asyncio
from typing import Optional, Tuple
import httpx

from app.models import (
    BoomiSettings,
    BoomiComponentInfo,
    PushToBoomiResponse,
)
from app.services.logging_service import log_activity


class BoomiAPIService:
    """Service for interacting with Boomi Platform API."""
    
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # seconds
    
    @staticmethod
    def _get_auth_header(settings: BoomiSettings) -> str:
        """Generate Basic auth header for Boomi API."""
        auth_string = f"BOOMI_TOKEN.{settings.username}:{settings.apiToken}"
        return base64.b64encode(auth_string.encode()).decode()
    
    @staticmethod
    async def create_component(
        settings: BoomiSettings,
        xml_content: str,
        customer_id: str,
        project_id: str
    ) -> Tuple[bool, str, Optional[BoomiComponentInfo]]:
        """
        Create a component in Boomi via API.
        
        Returns:
            Tuple of (success, message, component_info)
        """
        if not settings.accountId or not settings.username or not settings.apiToken:
            return False, "Boomi credentials not configured", None
        
        url = f"{settings.baseUrl}/{settings.accountId}/Component"
        headers = {
            "Authorization": f"Basic {BoomiAPIService._get_auth_header(settings)}",
            "Content-Type": "application/xml",
            "Accept": "application/json"
        }
        
        last_error = None
        
        for attempt in range(BoomiAPIService.MAX_RETRIES):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        url,
                        content=xml_content.encode('utf-8'),
                        headers=headers
                    )
                    
                    if response.status_code == 200 or response.status_code == 201:
                        # Parse response
                        try:
                            data = response.json()
                            component_id = data.get('componentId', '')
                            
                            component_info = BoomiComponentInfo(
                                componentId=component_id,
                                componentUrl=f"https://platform.boomi.com/AtomSphere.html#build;accountId={settings.accountId};components={component_id}",
                                folderPath=settings.defaultFolder,
                            )
                            
                            await log_activity(
                                action="boomi_push_success",
                                message=f"Component created: {component_id}",
                                category="push",
                                customer_id=customer_id,
                                project_id=project_id,
                                componentId=component_id
                            )
                            
                            return True, "Component created successfully", component_info
                            
                        except Exception as e:
                            # Response wasn't JSON, but still successful
                            component_info = BoomiComponentInfo(
                                componentId="unknown",
                                componentUrl="",
                                folderPath=settings.defaultFolder,
                            )
                            return True, "Component created (response parsing issue)", component_info
                    
                    elif response.status_code == 401:
                        return False, "Authentication failed - check Boomi credentials", None
                    
                    elif response.status_code == 403:
                        return False, "Access denied - check account permissions", None
                    
                    elif response.status_code == 400:
                        error_msg = response.text[:500] if response.text else "Bad request"
                        return False, f"Invalid request: {error_msg}", None
                    
                    else:
                        last_error = f"API returned status {response.status_code}: {response.text[:200]}"
                        
            except httpx.TimeoutException:
                last_error = "Request timed out"
            except httpx.ConnectError:
                last_error = "Could not connect to Boomi API"
            except Exception as e:
                last_error = str(e)
            
            # Exponential backoff
            if attempt < BoomiAPIService.MAX_RETRIES - 1:
                await asyncio.sleep(BoomiAPIService.RETRY_DELAY * (2 ** attempt))
        
        await log_activity(
            action="boomi_push_failed",
            message=f"Push failed after {BoomiAPIService.MAX_RETRIES} attempts: {last_error}",
            category="push",
            level="error",
            customer_id=customer_id,
            project_id=project_id
        )
        
        return False, f"Failed after {BoomiAPIService.MAX_RETRIES} attempts: {last_error}", None
    
    @staticmethod
    async def get_component(
        settings: BoomiSettings,
        component_id: str
    ) -> Tuple[bool, Optional[dict], str]:
        """
        Get a component from Boomi.
        
        Returns:
            Tuple of (success, component_data, error_message)
        """
        if not settings.accountId or not settings.username or not settings.apiToken:
            return False, None, "Boomi credentials not configured"
        
        url = f"{settings.baseUrl}/{settings.accountId}/Component/{component_id}"
        headers = {
            "Authorization": f"Basic {BoomiAPIService._get_auth_header(settings)}",
            "Accept": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    return True, response.json(), ""
                elif response.status_code == 404:
                    return False, None, "Component not found"
                else:
                    return False, None, f"API returned status {response.status_code}"
                    
        except Exception as e:
            return False, None, str(e)
    
    @staticmethod
    async def test_connection(settings: BoomiSettings) -> Tuple[bool, str]:
        """
        Test Boomi API connection.
        
        Returns:
            Tuple of (success, message)
        """
        if not settings.accountId or not settings.username or not settings.apiToken:
            return False, "Boomi credentials not configured"
        
        url = f"{settings.baseUrl}/{settings.accountId}/Account/{settings.accountId}"
        headers = {
            "Authorization": f"Basic {BoomiAPIService._get_auth_header(settings)}",
            "Accept": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    account_name = data.get('name', settings.accountId)
                    return True, f"Connected to Boomi account: {account_name}"
                elif response.status_code == 401:
                    return False, "Authentication failed"
                elif response.status_code == 403:
                    return False, "Access denied"
                else:
                    return False, f"API returned status {response.status_code}"
                    
        except httpx.TimeoutException:
            return False, "Connection timed out"
        except httpx.ConnectError:
            return False, "Could not connect to Boomi API"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    async def list_folders(
        settings: BoomiSettings,
        parent_id: Optional[str] = None
    ) -> Tuple[bool, list, str]:
        """
        List folders in Boomi account.
        
        Returns:
            Tuple of (success, folders, error_message)
        """
        if not settings.accountId or not settings.username or not settings.apiToken:
            return False, [], "Boomi credentials not configured"
        
        url = f"{settings.baseUrl}/{settings.accountId}/Folder/query"
        headers = {
            "Authorization": f"Basic {BoomiAPIService._get_auth_header(settings)}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        query = {"QueryFilter": {"expression": {"operator": "and", "nestedExpression": []}}}
        if parent_id:
            query["QueryFilter"]["expression"]["nestedExpression"].append({
                "argument": [parent_id],
                "operator": "EQUALS",
                "property": "parentId"
            })
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=query)
                
                if response.status_code == 200:
                    data = response.json()
                    folders = data.get('result', [])
                    return True, folders, ""
                else:
                    return False, [], f"API returned status {response.status_code}"
                    
        except Exception as e:
            return False, [], str(e)
