"""
Customer management API routes.
"""
from fastapi import APIRouter, HTTPException, status

from app.models import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerListResponse,
    ConnectionTestResult,
)
from app.services import CustomerService

router = APIRouter(prefix="/api/customers", tags=["customers"])


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(data: CustomerCreate):
    """Create a new customer."""
    return await CustomerService.create(data)


@router.get("", response_model=CustomerListResponse)
async def list_customers():
    """List all customers."""
    return await CustomerService.list_all()


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: str):
    """Get a customer by ID."""
    customer = await CustomerService.get(customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(customer_id: str, data: CustomerUpdate):
    """Update a customer."""
    customer = await CustomerService.update(customer_id, data)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(customer_id: str):
    """Delete a customer."""
    success = await CustomerService.delete(customer_id)
    if not success:
        raise HTTPException(status_code=404, detail="Customer not found")


@router.post("/{customer_id}/test-boomi", response_model=ConnectionTestResult)
async def test_boomi_connection(customer_id: str):
    """Test Boomi API connection for a customer."""
    return await CustomerService.test_boomi_connection(customer_id)


@router.post("/{customer_id}/test-llm", response_model=ConnectionTestResult)
async def test_llm_connection(customer_id: str):
    """Test LLM API connection for a customer."""
    return await CustomerService.test_llm_connection(customer_id)
