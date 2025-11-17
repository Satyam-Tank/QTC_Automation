from pydantic import BaseModel, Field
from typing import Optional, Literal, List

class QTCContainer(BaseModel):
    container_type: str = Field(..., description="e.g., 20GP, 40HC")
    quantity: int
    gross_weight_per_container: Optional[float] = None

class QTCFormData(BaseModel):
    inquiry_type: Literal["Budgetary", "Bid to win"] = Field(default="Bid to win")
    client_name: str
    product: Literal["Ocean", "Air", "Road", "Brokerage"]
    incoterms: str
    movement_type: Optional[str] = None

    # Example: Ocean FCL
    ocean_type: Optional[Literal["FCL", "LCL", "RORO", "Break Bulk"]] = None
    containers: List[QTCContainer] = []

    # Common fields
    port_of_loading: str
    port_of_discharge: str
    commodity: str = Field(..., description="This is mandatory, HIL if missing")
    freetime_requirement: int = Field(..., description="Mandatory, HIL if missing")
    dangerous_goods: bool = Field(default=False)
