from fastapi import FastAPI

app = FastAPI(title="Inventory and Order Management System")

@app.get("/")
def home():
    return {"message": "Inventory Management API is running"}
