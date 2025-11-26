"""Customer management API routes."""
from fastapi import APIRouter, HTTPException, status
from datetime import datetime
from app.models import CustomerCreate, CustomerUpdate, CustomerResponse, CustomerListResponse
from app.database import db

router = APIRouter(prefix="/api/customers", tags=["customers"])

@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(data: CustomerCreate):
    customer_dict = data.model_dump()
    customer_dict["createdAt"] = datetime.utcnow()
    customer_dict["updatedAt"] = datetime.utcnow()
    customer_dict["customerId"] = str(datetime.utcnow().timestamp())
    customer_dict["isActive"] = True
    
    result = await db.customers.insert_one(customer_dict)
    customer_dict["_id"] = str(result.inserted_id)
    
    return customer_dict

@router.get("", response_model=CustomerListResponse)
async def list_customers():
    customers = []
    async for customer in db.customers.find():
        customer["_id"] = str(customer["_id"])
        customer["customerId"] = customer.get("customerId", str(customer["_id"]))
        
        # FIX: Add missing fields for old customers
        if "createdAt" not in customer:
            customer["createdAt"] = datetime.utcnow()
        if "updatedAt" not in customer:
            customer["updatedAt"] = datetime.utcnow()
        if "isActive" not in customer:
            customer["isActive"] = True
            
        customers.append(customer)
    
    return {"customers": customers, "total": len(customers)}

@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: str):
    customer = await db.customers.find_one({"customerId": customer_id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    customer["_id"] = str(customer["_id"])
    
    # Add missing fields
    if "createdAt" not in customer:
        customer["createdAt"] = datetime.utcnow()
    if "updatedAt" not in customer:
        customer["updatedAt"] = datetime.utcnow()
    if "isActive" not in customer:
        customer["isActive"] = True
        
    return customer

@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(customer_id: str, data: CustomerUpdate):
    update_dict = data.model_dump(exclude_unset=True)
    update_dict["updatedAt"] = datetime.utcnow()
    
    result = await db.customers.update_one({"customerId": customer_id}, {"$set": update_dict})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    customer = await db.customers.find_one({"customerId": customer_id})
    customer["_id"] = str(customer["_id"])
    return customer

@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(customer_id: str):
    result = await db.customers.delete_one({"customerId": customer_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Customer not found")
    return None
