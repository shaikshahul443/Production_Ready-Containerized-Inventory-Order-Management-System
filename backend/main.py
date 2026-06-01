from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import models
import schemas
import crud
from database import engine, get_db

# Create database tables automatically
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Inventory & Order Management System API",
    description="Backend API for managing products, customers, orders, and stock levels.",
    version="1.0.0"
)

# CORS configurations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper function to format order response
def serialize_order(order: models.Order) -> schemas.OrderResponse:
    return schemas.OrderResponse(
        id=order.id,
        customer_id=order.customer_id,
        customer_name=order.customer.name,
        customer_email=order.customer.email,
        order_date=order.order_date,
        status=order.status,
        total_price=order.total_price,
        items=[
            schemas.OrderItemResponse(
                id=item.id,
                product_id=item.product_id,
                product_name=item.product.name if item.product else "Unknown Product",
                product_sku=item.product.sku if item.product else "N/A",
                quantity=item.quantity,
                unit_price=item.unit_price
            )
            for item in order.items
        ]
    )

# ----------------- BASE ROUTE -----------------
@app.get("/")
def read_root():
    return {"message": "Welcome to the Inventory & Order Management API. Access /docs for swagger docs."}

# ----------------- DASHBOARD ENDPOINTS -----------------
@app.get("/api/dashboard", status_code=status.HTTP_200_OK)
@app.get("/dashboard", status_code=status.HTTP_200_OK)
def get_dashboard(db: Session = Depends(get_db)):
    metrics = crud.get_dashboard_metrics(db)
    # Serialize recent orders in dashboard
    metrics["recent_orders"] = [serialize_order(order) for order in metrics["recent_orders"]]
    return metrics

# ----------------- PRODUCT ENDPOINTS -----------------
@app.get("/api/products", response_model=List[schemas.ProductResponse])
@app.get("/products", response_model=List[schemas.ProductResponse])
def read_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_products(db, skip=skip, limit=limit)

@app.get("/api/products/{product_id}", response_model=schemas.ProductResponse)
@app.get("/products/{product_id}", response_model=schemas.ProductResponse)
def read_product(product_id: int, db: Session = Depends(get_db)):
    db_product = crud.get_product(db, product_id)
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product

@app.post("/api/products", response_model=schemas.ProductResponse, status_code=status.HTTP_201_CREATED)
@app.post("/products", response_model=schemas.ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    return crud.create_product(db, product)

@app.put("/api/products/{product_id}", response_model=schemas.ProductResponse)
@app.put("/products/{product_id}", response_model=schemas.ProductResponse)
def update_product(product_id: int, product: schemas.ProductUpdate, db: Session = Depends(get_db)):
    return crud.update_product(db, product_id, product)

@app.delete("/api/products/{product_id}", response_model=schemas.ProductResponse)
@app.delete("/products/{product_id}", response_model=schemas.ProductResponse)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    return crud.delete_product(db, product_id)

# ----------------- CUSTOMER ENDPOINTS -----------------
@app.get("/api/customers", response_model=List[schemas.CustomerResponse])
@app.get("/customers", response_model=List[schemas.CustomerResponse])
def read_customers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_customers(db, skip=skip, limit=limit)

@app.get("/api/customers/{customer_id}", response_model=schemas.CustomerResponse)
@app.get("/customers/{customer_id}", response_model=schemas.CustomerResponse)
def read_customer(customer_id: int, db: Session = Depends(get_db)):
    db_customer = crud.get_customer(db, customer_id)
    if db_customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return db_customer

@app.post("/api/customers", response_model=schemas.CustomerResponse, status_code=status.HTTP_201_CREATED)
@app.post("/customers", response_model=schemas.CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    return crud.create_customer(db, customer)

@app.put("/api/customers/{customer_id}", response_model=schemas.CustomerResponse)
@app.put("/customers/{customer_id}", response_model=schemas.CustomerResponse)
def update_customer(customer_id: int, customer: schemas.CustomerUpdate, db: Session = Depends(get_db)):
    return crud.update_customer(db, customer_id, customer)

@app.delete("/api/customers/{customer_id}", response_model=schemas.CustomerResponse)
@app.delete("/customers/{customer_id}", response_model=schemas.CustomerResponse)
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    return crud.delete_customer(db, customer_id)

# ----------------- ORDER ENDPOINTS -----------------
@app.get("/api/orders", response_model=List[schemas.OrderResponse])
@app.get("/orders", response_model=List[schemas.OrderResponse])
def read_orders(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    db_orders = crud.get_orders(db, skip=skip, limit=limit)
    return [serialize_order(order) for order in db_orders]

@app.get("/api/orders/{order_id}", response_model=schemas.OrderResponse)
@app.get("/orders/{order_id}", response_model=schemas.OrderResponse)
def read_order(order_id: int, db: Session = Depends(get_db)):
    order = crud.get_order(db, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return serialize_order(order)

@app.post("/api/orders", response_model=schemas.OrderResponse, status_code=status.HTTP_201_CREATED)
@app.post("/orders", response_model=schemas.OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(order: schemas.OrderCreate, db: Session = Depends(get_db)):
    db_order = crud.create_order(db, order)
    return serialize_order(db_order)

@app.put("/api/orders/{order_id}/status", response_model=schemas.OrderResponse)
@app.put("/orders/{order_id}/status", response_model=schemas.OrderResponse)
def update_order_status(order_id: int, payload: schemas.OrderUpdateStatus, db: Session = Depends(get_db)):
    db_order = crud.update_order_status(db, order_id, payload.status)
    return serialize_order(db_order)

@app.delete("/api/orders/{order_id}", response_model=schemas.OrderResponse)
@app.delete("/orders/{order_id}", response_model=schemas.OrderResponse)
def delete_order(order_id: int, db: Session = Depends(get_db)):
    db_order = crud.delete_order(db, order_id)
    return serialize_order(db_order)
