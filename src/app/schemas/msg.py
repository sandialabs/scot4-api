from pydantic import BaseModel, Field
from typing import Annotated


class Msg(BaseModel):
    msg: Annotated[str, Field(...)]
