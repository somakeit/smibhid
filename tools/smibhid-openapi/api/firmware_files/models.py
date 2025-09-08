from typing import Literal, Annotated

from pydantic import BaseModel, Field


class FirmwareFilesRequest(BaseModel):
    action: Literal["add", "remove"]
    url: Annotated[str, Field(examples=["https://github.com/somakeit/smibhid/blob/master/src/main.py"])]
