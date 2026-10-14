from pydantic import BaseModel, ConfigDict


class PriceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticker: str
    price: float
    timestamp: int
