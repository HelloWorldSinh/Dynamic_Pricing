from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class SkuMappingPairResponse(BaseModel):
    """Phan hoi mot cap doi soat SKU giua FPT Shop va doi thu."""
    id: str
    fpt_sku: str
    fpt_name: str
    fpt_part_number: Optional[str] = None
    fpt_price: int
    competitor_source: str
    competitor_name: str
    competitor_url: str
    competitor_price: int
    competitor_part_number: Optional[str] = None
    confidence_score: float
    matched_attributes: List[str]
    differing_attributes: List[str]
    status: str

    model_config = ConfigDict(from_attributes=True)
