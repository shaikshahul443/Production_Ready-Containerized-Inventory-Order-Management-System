from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException
from decimal import Decimal
import models
import schemas

# ----------------- PRODUCT CRUD -----------------
def get_product(db: Session, product_id: int):
    return db.query(models.Product).filter(models.Product.id == product_id).first()

def get_product_by_sku(db: Session, sku: str):
    return db.query(models.Product).filter(models.Product.sku == sku.upper()).first()

def get_products(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Product).order_by(models.Product.id).offset(skip).limit(limit).all()

def create_product(db: Session, product: schemas.ProductCreate):
    # Check if SKU is unique
    existing = get_product_by_sku(db, product.sku)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Product with SKU '{product.sku}' already exists."
        )
    db_product = models.Product(
        sku=product.sku.upper(),
        name=product.name,
        description=product.description,
        price=product.price,
        stock=product.stock
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def update_product(db: Session, product_id: int, product_data: schemas.ProductUpdate):
    db_product = get_product(db, product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    update_dict = product_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(db_product, key, value)
        
    db.commit()
    db.refresh(db_product)
    return db_product

def delete_product(db: Session, product_id: int):
    db_product = get_product(db, product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(db_product)
    db.commit()
    return db_product

# ----------------- CUSTOMER CRUD -----------------
def get_customer(db: Session, customer_id: int):
    return db.query(models.Customer).filter(models.Customer.id == customer_id).first()

def get_customer_by_email(db: Session, email: str):
    return db.query(models.Customer).filter(func.lower(models.Customer.email) == email.lower()).first()

def get_customers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Customer).order_by(models.Customer.id).offset(skip).limit(limit).all()

def create_customer(db: Session, customer: schemas.CustomerCreate):
    # Check if Email is unique
    existing = get_customer_by_email(db, customer.email)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Customer with email '{customer.email}' already exists."
        )
    db_customer = models.Customer(
        name=customer.name,
        email=customer.email,
        phone=customer.phone
    )
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer

def update_customer(db: Session, customer_id: int, customer_data: schemas.CustomerUpdate):
    db_customer = get_customer(db, customer_id)
    if not db_customer:
        raise HTTPException(status_code=404, detail="Customer not found")
        
    update_dict = customer_data.model_dump(exclude_unset=True)
    
    if "email" in update_dict:
        # Check uniqueness of new email
        existing = get_customer_by_email(db, update_dict["email"])
        if existing and existing.id != customer_id:
            raise HTTPException(
                status_code=400,
                detail=f"Customer with email '{update_dict['email']}' already exists."
            )
            
    for key, value in update_dict.items():
        setattr(db_customer, key, value)
        
    db.commit()
    db.refresh(db_customer)
    return db_customer

def delete_customer(db: Session, customer_id: int):
    db_customer = get_customer(db, customer_id)
    if not db_customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    db.delete(db_customer)
    db.commit()
    return db_customer

# ----------------- ORDER CRUD -----------------
def get_order(db: Session, order_id: int):
    return db.query(models.Order).filter(models.Order.id == order_id).first()

def get_orders(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Order).order_by(models.Order.order_date.desc()).offset(skip).limit(limit).all()

def create_order(db: Session, order_data: schemas.OrderCreate):
    # Verify customer exists
    customer = db.query(models.Customer).filter(models.Customer.id == order_data.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
        
    db_items = []
    total_price = Decimal("0.00")
    
    # We lock selected product rows to prevent concurrent race conditions on stock reduction
    for item in order_data.items:
        product = db.query(models.Product).filter(models.Product.id == item.product_id).with_for_update().first()
        if not product:
            raise HTTPException(
                status_code=404, 
                detail=f"Product with ID {item.product_id} not found"
            )
            
        # Validate stock
        if product.stock < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for product '{product.name}' (SKU: {product.sku}). Requested: {item.quantity}, Available: {product.stock}"
            )
            
        # Deduct stock
        product.stock -= item.quantity
        
        # Calculate item price
        item_price = product.price * item.quantity
        total_price += item_price
        
        db_items.append(
            models.OrderItem(
                product_id=product.id,
                quantity=item.quantity,
                unit_price=product.price
            )
        )
        
    # Create the Order
    db_order = models.Order(
        customer_id=order_data.customer_id,
        status="Pending",
        total_price=total_price
    )
    db.add(db_order)
    db.flush() # assign ID to db_order
    
    # Add items
    for db_item in db_items:
        db_item.order_id = db_order.id
        db.add(db_item)
        
    db.commit()
    db.refresh(db_order)
    return db_order

def update_order_status(db: Session, order_id: int, status: str):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    old_status = order.status
    if old_status == status:
        return order
        
    # Restoring stock if order gets cancelled
    if status == "Cancelled" and old_status != "Cancelled":
        for item in order.items:
            product = db.query(models.Product).filter(models.Product.id == item.product_id).with_for_update().first()
            if product:
                product.stock += item.quantity
                
    # Deducting stock again if order gets reinstated from Cancelled state
    elif old_status == "Cancelled" and status != "Cancelled":
        for item in order.items:
            product = db.query(models.Product).filter(models.Product.id == item.product_id).with_for_update().first()
            if not product:
                raise HTTPException(
                    status_code=404,
                    detail=f"Product with ID {item.product_id} no longer exists."
                )
            if product.stock < item.quantity:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot reinstate order. Product '{product.name}' has insufficient stock. (Requested: {item.quantity}, Available: {product.stock})"
                )
            product.stock -= item.quantity
            
    order.status = status
    db.commit()
    db.refresh(order)
    return order

def delete_order(db: Session, order_id: int):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    # If we delete a Pending/Completed order, let's restore the stock first!
    if order.status != "Cancelled":
        for item in order.items:
            product = db.query(models.Product).filter(models.Product.id == item.product_id).with_for_update().first()
            if product:
                product.stock += item.quantity
                
    db.delete(order)
    db.commit()
    return order

# ----------------- DASHBOARD METRICS -----------------
def get_dashboard_metrics(db: Session):
    total_products = db.query(func.count(models.Product.id)).scalar() or 0
    total_customers = db.query(func.count(models.Customer.id)).scalar() or 0
    total_orders = db.query(func.count(models.Order.id)).scalar() or 0
    
    # Revenue (from Completed and Pending orders, exclude Cancelled)
    revenue = db.query(func.sum(models.Order.total_price)).filter(models.Order.status != "Cancelled").scalar() or Decimal("0.00")
    
    # Low stock count (stock < 5)
    low_stock_products = db.query(models.Product).filter(models.Product.stock < 5).all()
    
    # Recent orders (last 5)
    recent_orders = db.query(models.Order).order_by(models.Order.order_date.desc()).limit(5).all()
    
    return {
        "total_products": total_products,
        "total_customers": total_customers,
        "total_orders": total_orders,
        "total_revenue": revenue,
        "low_stock_count": len(low_stock_products),
        "low_stock_items": [
            {"id": p.id, "sku": p.sku, "name": p.name, "stock": p.stock}
            for p in low_stock_products
        ],
        "recent_orders": recent_orders
    }
