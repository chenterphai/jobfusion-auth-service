from typing import TypeVar, Generic, List, Union, Optional
from pydantic import BaseModel

T = TypeVar("T")

class Status(BaseModel):
    code: int
    msg: str
    status: str

class Result(BaseModel, Generic[T]):
    data: Optional[Union[T, List[T]]] = None

class ResponseModel(BaseModel, Generic[T]):
    status: Status
    result: Result[T]