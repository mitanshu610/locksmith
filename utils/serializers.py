from typing import List, Dict, Optional, Union
from uuid import uuid4

from pydantic.fields import Field
from pydantic.main import BaseModel


class ResponseData(BaseModel):
    identifier: str = Field(default_factory=lambda: str(uuid4()))
    success: bool
    message: Optional[str] = None
    errors: Optional[List] = Field(None)
    data: Optional[Union[List, Dict]] = Field(None)

    def dict(self, *args, **kwargs):
        return super().model_dump(*args, **kwargs)
