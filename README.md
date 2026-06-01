# StockFlow: Inventory & Order Management System

StockFlow is a modern, responsive, and transactional Inventory & Order Management System. It features a Python **FastAPI** backend, a **React (Vite)** frontend with dark-mode glassmorphic aesthetics, and a **PostgreSQL** database. 

## Features

1. **Operations Dashboard**: Quick overview of total revenue, active orders, product SKUs, client counts, real-time low stock warnings, and recent transaction logs.
2. **Product Catalog**: SKU uniqueness validation, real-time stock status color indicators (green/yellow/red), pricing, and description management.
3. **Customer Directory**: Customer profiles with unique email validation.
4. **Order Manager**: A shopping cart order builder with:
   - Real-time stock validation (disables order submission and warns users if quantity exceeds available stock).
   - Automated inventory stock reduction when orders are successfully placed.
   - Restoring stock to inventory when orders are set to `Cancelled` or deleted.

---

## Technical Stack

- **Backend**: FastAPI, SQLAlchemy, Pydantic, Uvicorn, PostgreSQL (Psycopg2)
- **Frontend**: React (Vite), Lucide-react (for iconography), Custom Glassmorphic Vanilla CSS (No Tailwind)
- **Containerization**: Docker, Docker Compose, Nginx (frontend reverse proxy)

---

## Quick Start (Local Run)

Ensure you have **Docker** and **Docker Compose** installed on your machine.

1. **Spin up the Services**:
   From the root folder containing `docker-compose.yml`, run:
   ```bash
   docker compose up --build
   ```

2. **Access the App**:
   - **React Frontend**: Navigate to [http://localhost:3000](http://localhost:3000)
   - **FastAPI API & Documentation (Swagger)**: Navigate to [http://localhost:8000/docs](http://localhost:8000/docs)
   - **PostgreSQL Database**: Port `5432` (connect using credentials inside `.env`)

---

## Business Rules & Implementation Details

- **SKU Uniqueness**: Managed via database constraint (`unique=True`) and backend CRUD checks. Product SKUs are auto-normalized to uppercase.
- **Customer Email Uniqueness**: Enforced in database schema and API validators.
- **Inventory Control**: Transactional row-locking (`with_for_update()`) prevents race conditions during order placement. Stock deductions occur within database transactions; if any items fail verification, the entire operation rolls back.
- **Stock Reversion**: If an order status changes to `Cancelled` or is deleted entirely, inventory is safely returned to stock. Reinstating a cancelled order checks and reserves stock again.

---

## Deployment Guide (Free Hosting Platforms)

To deploy the application to public URLs, you can use the following free or developer-tier platforms:

### 1. Database (PostgreSQL)
- **Supabase** or **Neon.tech**:
  1. Register for a free account.
  2. Create a new PostgreSQL database instance.
  3. Copy the connection string.
  4. Paste this connection string under the `DATABASE_URL` environment variable inside your backend hosting settings.

### 2. Backend (FastAPI)
- **Render** or **Railway**:
  1. Create a Web Service pointing to your GitHub repository.
  2. Set the build command root directory to `backend`.
  3. Select **Docker** as the environment (it will auto-detect `backend/Dockerfile`).
  4. Under environment variables, define `DATABASE_URL` with your Neon/Supabase DB URL.
  5. Deploy. You will receive a public URL (e.g. `https://stockflow-backend.onrender.com`).

### 3. Frontend (React Vite)
- **Vercel** or **Netlify**:
  1. Create a project pointing to your GitHub repo.
  2. Select the `frontend` folder as the root directory.
  3. Configure the framework preset as **Vite**.
  4. Add an environment variable: `VITE_API_URL=https://your-backend-render-url.com` (your deployed backend API URL).
  5. Deploy. You will receive a public URL (e.g. `https://stockflow.vercel.app`).

### 4. Docker Images
- To build and submit your images to **Docker Hub**:
  ```bash
  # Build backend
  docker build -t your-dockerhub-username/stockflow-backend:latest ./backend
  docker push your-dockerhub-username/stockflow-backend:latest

  # Build frontend
  docker build -t your-dockerhub-username/stockflow-frontend:latest ./frontend
  docker push your-dockerhub-username/stockflow-frontend:latest
  ```
