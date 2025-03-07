import re
from typing import Annotated
from fastapi import FastAPI, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
import pandas as pd
from pydantic import BaseModel
import json
import requests

app = FastAPI(
    title="Mito Weekly Planner",
    description="App that lets you efficiently plan out which stores to go based on your location and urgency of visits.",
)

StaticFiles.is_not_modified = lambda self, *args, **kwargs: False

app.mount("/static", StaticFiles(directory="public/static"), name="static")


@app.get("/")
async def root():
    return FileResponse("public/static/index.html")


class R(BaseModel):
    q: str | None = None


@app.post("/api/search")
async def search(req: R):
    q = req.q

    predictions = search_address(q)

    htmlElements = [
        f"""
            <button type="button"
                hx-post="/api/setStartingAddress"
                hx-ext="json-enc"
                hx-swap="outerHTML"
                hx-target="#res-container"
                hx-vals='{{"p": "{p}"}}'
                hx-params="not q"
            >
                {p}
            </button>
        """
        for p in predictions
    ]

    return HTMLResponse(
        f"""
          <div
            id="starting_address_results"
            style="visibility: {"hidden" if len(htmlElements) == 0 else "visible"}"
          > {"".join(htmlElements)}
          </div>
        """
    )


def search_address(starting_address: str | None) -> list[str]:
    if starting_address is None or starting_address == "":
        return []

    print("request sent")

    res = requests.post(
        url="https://places.googleapis.com/v1/places:autocomplete",
        json={
            "input": starting_address,
            "locationBias": {
                "rectangle": {
                    "high": {
                        "latitude": 45.71429912457236,
                        "longitude": -74.04305828564718,
                    },
                    "low": {
                        "latitude": 45.406702295712975,
                        "longitude": -73.44293059335915,
                    },
                }
            },
        },
        headers={
            "X-Goog-Api-Key": "AIzaSyCQrnHYiPKBQO0ImU926iIECNkzH3Pp92g",
            "X-Goog-FieldMask": "suggestions.placePrediction.text.text",
            "Content-Type": "application/json",
        },
    )

    if not res.ok:
        return []

    suggestions = res.json().get("suggestions")

    if suggestions is None:
        return []

    return [sug["placePrediction"]["text"]["text"] for sug in suggestions]


class Store(R):
    important: str | None = None


@app.post("/api/store")
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
                        <label for="store{stores.loc[i]["No Mag."]}">Urgent</label>
                        <input type="checkbox" id="store{stores.loc[i]["No Mag."]}" onchange="toggleImportant({stores.loc[i]["No Mag."]})" {"checked" if stores.loc[i]["No Mag."] in important else ""} />
                    </div>
                </div>
                <p class="store-card-info">{stores.loc[i]["Nom Mag."]}</p>
                <p class="store-card-info">{stores.loc[i]["Adresse Mag."]}, {stores.loc[i]["Ville"]}, {stores.loc[i]["Postal"]}</p>
            </div>
        """
        for i in stores.index
    ]

    return HTMLResponse("".join(htmlStores))


def search_store(store: str | None) -> pd.DataFrame:
    data = pd.read_csv("public/static/stores_location.csv")

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


class SetAddrModel(BaseModel):
    p: str | None = None


@app.post("/api/setStartingAddress")
async def setStartingAddress(req: SetAddrModel):
    p = req.p

    return HTMLResponse(f"""
        <div 
            class="must-visit-card"
            id="selected_address"
        >
          <i
            class="fa-solid fa-xmark"
            style="color: var(--secondary-text)"
            hx-get="/api/removeStartingAddress"
            hx-trigger="click"
            hx-swap="outerHTML"
            hx-target="#selected_address"
          ></i>
          <span>{p}</span>
        </div>
    """)


@app.get("/api/removeStartingAddress")
async def removeStartingAddress():
    return HTMLResponse("""
      <div id="res-container">
        <input
          id="starting_address"
          name="q"
          type="text"
          placeholder="Search..."
          autocomplete="off"
          hx-trigger="keyup changed delay:500"
          hx-post="/api/search"
          hx-sync="closest form:abort"
          hx-ext="json-enc"
          hx-target="#starting_address_results"
          hx-swap="outerHTML"
        />
        <button type="submit">
          <i class="fa-solid fa-magnifying-glass-location"></i>
        </button>
        <div
          id="starting_address_results"
          style="visibility: hidden"
        ></div>
      </div>
    """)
