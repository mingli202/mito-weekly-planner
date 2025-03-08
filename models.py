from fastapi import Response
from pydantic import BaseModel


class Req(BaseModel):
    q: str | None = None


class SetAddrModel(BaseModel):
    p: str | None = None
    placeId: str | None = None


class Res(BaseModel):
    html: str = ""
    data: dict = {}


class StoreInfo(BaseModel):
    number: int
    name: str
    addr: str
    city: str
    postalCode: str
