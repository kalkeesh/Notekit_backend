from pydantic import BaseModel, Field
from typing import Optional

class Note(BaseModel):
    id: Optional[str] = Field(default=None)
    title: str
    content: str


    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            # converts ObjectId to string
            # helpful for returning valid JSON
        }
