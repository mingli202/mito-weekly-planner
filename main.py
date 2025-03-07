import re
from typing import Annotated
from fastapi import FastAPI, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
import pandas as pd
from pydantic import BaseModel
import json

app = FastAPI(
    title="Mito Weekly Planner",
    description="App that lets you efficiently plan out which stores to go based on your location and urgency of visits.",
)

app.mount("/static", StaticFiles(directory="public/static", html=True), name="static")


@app.get("/")
async def root():
    return FileResponse("public/static/index.html")


@app.get("/search")
async def search(q: str | None = None):
    if q and q != "":
        return search_address(q)

    return HTMLResponse("")


def search_address(starting_address: str) -> JSONResponse:
    return JSONResponse({"address": "hellow orld"})


class Store(BaseModel):
    q: str | None = None
    important: str | None = None


@app.post("/store")
async def store_search(
    store: Store,
):
    stores = search_store(store.q)

    important = []
    if store.important:
        important = json.loads(store.important)

    htmlStores = [
        f"""
            <div class="store-card">
                <div class="store-header">
                    <p>#{stores.loc[i]["No Mag."]}</p>
                    <div class="store-card-must-visit">
                        <label for="store{stores.loc[i]["No Mag."]}">Must visit</label>
                        <input type="checkbox" id="store{stores.loc[i]["No Mag."]}" onchange="toggleImportant({stores.loc[i]["No Mag."]})" {"checked" if stores.loc[i]["No Mag."] in important else ""} />
                    </div>
                </div>
                <p class="store-card-info">{stores.loc[i]["Nom Mag."]}</p>
                <p class="store-card-info">{stores.loc[i]["Adresse Mag."]}, {stores.loc[i]["Ville"]}, {stores.loc[i]["Postal"]}</p>
            </div>
        """
        for i in stores.index
    ]

    return HTMLResponse("\n".join(htmlStores))


def search_store(store: str | None) -> pd.DataFrame:
    data = pd.read_csv("public/stores_location.csv")

    if not store or store == "":
        return data

    data = data.loc[
        [
            all(
                any(
                    re.search(_store, s, re.I) is not None
                    for s in [
                        str(data.loc[i]["No Mag."]),
                        data.loc[i]["Nom Mag."],
                        data.loc[i]["Adresse Mag."],
                        data.loc[i]["Ville"],
                        data.loc[i]["Postal"],
                    ]
                )
                for _store in store.split(" ")
            )
            if not store.startswith("#")
            else str(data.loc[i]["No Mag."]).startswith(store[1:])
            for i in data.index
        ]
    ]

    return data
