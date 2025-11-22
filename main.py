import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from database import db, create_document, get_documents
from schemas import Product, Order

app = FastAPI(title="CARTX API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "CARTX backend is running"}

# Products
@app.get("/api/products")
def list_products(category: Optional[str] = None):
    try:
        query = {"category": category} if category else {}
        products = get_documents("product", query)
        for p in products:
            p["_id"] = str(p.get("_id"))
        return {"items": products}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/products")
def create_product(payload: Product):
    try:
        _id = create_document("product", payload)
        return {"_id": _id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Seed sample products
@app.post("/api/seed")
def seed_products():
    try:
        existing = get_documents("product", {}, limit=1)
        if existing:
            return {"status": "already-seeded"}
        samples = [
            Product(title="Orion Headphones", description="High-fidelity wireless headphones with noise cancellation.", price=129.99, category="Audio", image="https://images.unsplash.com/photo-1518443895470-87f48ac871ec?q=80&w=1600&auto=format&fit=crop", in_stock=True),
            Product(title="Nova Smartwatch", description="AMOLED display, 7-day battery, fitness tracking.", price=199.00, category="Wearables", image="https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?q=80&w=1600&auto=format&fit=crop", in_stock=True),
            Product(title="Flux Portable Speaker", description="Compact speaker with powerful bass and orange accent ring.", price=89.50, category="Audio", image="https://images.unsplash.com/photo-1519677100203-a0e668c92439?q=80&w=1600&auto=format&fit=crop", in_stock=True),
            Product(title="Pulse Mechanical Keyboard", description="Hot-swappable switches, RGB, USB-C.", price=149.00, category="Peripherals", image="https://images.unsplash.com/photo-1517336714731-489689fd1ca8?q=80&w=1600&auto=format&fit=crop", in_stock=True),
        ]
        ids = []
        for s in samples:
            ids.append(create_document("product", s))
        return {"status": "seeded", "count": len(ids), "ids": ids}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Orders
@app.post("/api/orders")
def create_order(payload: Order):
    try:
        _id = create_document("order", payload)
        return {"_id": _id, "status": "received"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/orders")
def list_orders(limit: int = 50):
    try:
        docs = get_documents("order", {}, limit)
        for d in docs:
            d["_id"] = str(d.get("_id"))
        return {"items": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Schemas endpoint for viewer
@app.get("/schema")
def get_schema():
    from inspect import getmembers, isclass
    import schemas as schema_module

    def model_to_dict(model_cls):
        fields = {}
        for name, field in model_cls.model_fields.items():
            fields[name] = {
                "type": str(field.annotation),
                "required": field.is_required(),
                "default": None if field.is_required() else field.default,
                "description": getattr(field.field_info, "description", None)
            }
        return {
            "name": model_cls.__name__,
            "collection": model_cls.__name__.lower(),
            "fields": fields
        }

    models = [m for _, m in getmembers(schema_module) if isclass(m) and issubclass(m, BaseModel) and m is not BaseModel]
    return {"models": [model_to_dict(m) for m in models]}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"

            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
