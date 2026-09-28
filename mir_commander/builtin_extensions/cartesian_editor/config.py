from pydantic import BaseModel, Field


class Config(BaseModel):
    decimals: int = Field(default=6, ge=1, le=15, description="Number of decimal places to display")
