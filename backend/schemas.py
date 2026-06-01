from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

# ----------------- PRODUCT SCHEMAS -----------------
class ProductBase(BaseModel):
    sku: str = Field(..., min_length=3, max_length=50, description="Unique SKU code")
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    price: Decimal = Field(..., gt=0, decimal_places=2)
    stock: int = Field(..., ge=0)

    @field_validator("sku")
    @classmethod
    def validate_sku(cls, value: str):
        # SKUs should be alphanumeric, can contain dashes or underscores
        import re
        if not re.match(r"^[A-Za-z0-9-_]+$", value):
            raise ValueError("SKU must contain only letters, numbers, dashes, and underscores")
        return value.upper()

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    stock: Optional[int] = Field(None, ge=0)

class ProductResponse(ProductBase):
    id: int

    class Config:
        from_attributes = True

# ----------------- CUSTOMER SCHEMAS -----------------
class CustomerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

class CustomerResponse(CustomerBase):
    id: int

    class Config:
        from_attributes = True

# ----------------- ORDER ITEM SCHEMAS -----------------
class OrderItemBase(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)

class OrderItemCreate(OrderItemBase):
    pass

class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    product_sku: str
    quantity: int
    unit_price: Decimal

    class Config:
        from_attributes = True

# ----------------- ORDER SCHEMAS -----------------
class OrderCreate(BaseModel):
    customer_id: int
    items: List[OrderItemCreate] = Field(..., min_length=1)

class OrderUpdateStatus(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str):
        allowed = ["Pending", "Completed", "Cancelled"]
        if value not in allowed:
            raise ValueError(f"Status must be one of {allowed}")
        return value

class OrderResponse(BaseModel):
    id: int
    customer_id: int
    customer_name: str
    customer_email: str
    order_date: datetime
    status: str
    total_price: Decimal
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True
