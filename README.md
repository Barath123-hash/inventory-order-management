# Inventory and Order Management System

## Project Overview
A backend microservices-based Inventory and Order Management System built using Python, FastAPI, and SQLite.

## Technologies Used
- Python
- FastAPI
- SQLite
- SQLAlchemy
- JWT Authentication
- HTTPX
- Postman
- Git and GitHub

## Microservices
1. Auth Service — Port 8001
2. Product Service — Port 8002
3. Inventory Service — Port 8003
4. Cart Service — Port 8004
5. Order Service — Port 8005
6. Payment Service — Port 8006
7. Notification Service — Port 8007
8. Review Service — Port 8008
9. Coupon Service — Port 8009
10. Return Service — Port 8010
11. Analytics Service — Port 8011
12. API Gateway — Port 8000

## Features
- User registration and login
- Product management
- Inventory management
- Shopping cart
- Order creation and status management
- Mock payment processing
- Notifications
- Product reviews
- Coupon management
- Return requests
- Order analytics
- API Gateway request forwarding

## How to Run
Activate the virtual environment:

```bash
source venv/bin/activate
```

Start each microservice from the project root in a separate terminal:

```bash
uvicorn app.main:app --reload --port 8001 --app-dir auth-service
uvicorn app.main:app --reload --port 8002 --app-dir product-service
uvicorn app.main:app --reload --port 8003 --app-dir inventory-service
uvicorn app.main:app --reload --port 8004 --app-dir cart-service
uvicorn app.main:app --reload --port 8005 --app-dir order-service
uvicorn app.main:app --reload --port 8006 --app-dir payment-service
uvicorn app.main:app --reload --port 8007 --app-dir notification-service
uvicorn app.main:app --reload --port 8008 --app-dir review-service
uvicorn app.main:app --reload --port 8009 --app-dir coupon-service
uvicorn app.main:app --reload --port 8010 --app-dir return-service
uvicorn app.main:app --reload --port 8011 --app-dir analytics-service
uvicorn app.main:app --reload --port 8000 --app-dir api-gateway
```

## API Documentation
Once a service is running, open its `/docs` endpoint in the browser.

API Gateway: http://127.0.0.1:8000/docs

## Notes
Payments use mock processing for testing. This project is a backend implementation.
