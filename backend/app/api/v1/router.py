from fastapi import APIRouter
from app.api.v1.endpoints import crawl, products

api_router = APIRouter()
api_router.include_router(crawl.router, prefix="/crawl", tags=["Crawling Engine (PBI-001 & PBI-004)"])
api_router.include_router(products.router, prefix="/products", tags=["Product Catalog (FPT Baseline)"])
