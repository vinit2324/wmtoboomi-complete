"""
Customer data models for multi-customer management.
"""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


class BoomiSettings(BaseModel):
    """Boomi API connection settings."""
    accountId: str = ""
    username: str = ""
    apiToken: str = ""  # Will be encrypted
    baseUrl: str = "https://api.boomi.com/api/rest/v1"
    defaultFolder: str = "Jade Global, Inc./MigrationPoC"


class LLMSettings(BaseModel):
    """LLM provider settings."""
    provider: Literal["openai", "anthropic", "gemini", "ollama"] = "openai"
    apiKey: str = ""  # Will be encrypted
    baseUrl: str = ""  # For Ollama or custom endpoints
    model: str = "gpt-4-turbo"
    temperature: float = 0.7


class CustomerSettings(BaseModel):
    """Combined customer settings."""
    boomi: BoomiSettings = Field(default_factory=BoomiSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)


class CustomerCreate(BaseModel):
    """Request model for creating a customer."""
    customerName: str = Field(..., min_length=1, max_length=200)
    settings: Optional[CustomerSettings] = None


class CustomerUpdate(BaseModel):
    """Request model for updating a customer."""
    customerName: Optional[str] = Field(None, min_length=1, max_length=200)
    settings: Optional[CustomerSettings] = None


class CustomerResponse(BaseModel):
    """Response model for customer data."""
    customerId: str
    customerName: str
    createdAt: datetime
    updatedAt: datetime
    settings: CustomerSettings
    isActive: bool = True


class CustomerListResponse(BaseModel):
    """Response model for list of customers."""
    customers: list[CustomerResponse]
    total: int


class ConnectionTestResult(BaseModel):
    """Result of a connection test."""
    success: bool
    message: str
    details: Optional[dict] = None
