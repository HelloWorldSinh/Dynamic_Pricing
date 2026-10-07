from fastapi import APIRouter
from app.api.v1.endpoints import crawl, products, pricing, matching

api_router = APIRouter()
api_router.include_router(crawl.router, prefix="/crawl", tags=["Crawling Engine (PBI-001 & PBI-004)"])
api_router.include_router(products.router, prefix="/products", tags=["Product Catalog (FPT Baseline)"])
api_router.include_router(pricing.router, prefix="/pricing", tags=["Dynamic Pricing Engine (PBI-010, PBI-011, PBI-016)"])
api_router.include_router(matching.router, prefix="/matching", tags=["SKU Matching Review Queue (PBI-006, PBI-007, PBI-008)"])

