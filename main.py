import re
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
import pandas as pd
import json
import requests
from pydantic_settings import BaseSettings, SettingsConfigDict

from models import Req, Res, SetAddrModel


class Settings(BaseSettings):
    gmapsApiKey: str = ""
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
app = FastAPI(
    title="Mito Weekly Planner",
    description="App that lets you efficiently plan out which stores to go based on your location and urgency of visits.",
)

StaticFiles.is_not_modified = lambda self, *args, **kwargs: False

app.mount("/static", StaticFiles(directory="public/static"), name="static")

starting_address = ""


@app.get("/")
async def root():
    return FileResponse("public/static/index.html")


@app.post("/api/search")
async def search(req: Req) -> Res:
    q = req.q

    predictions = search_address(q)

    htmlElements = [
        f"""
            <button type="button"
                hx-post="/api/setStartingAddress"
                hx-ext="json-enc"
                hx-swap="outerHTML"
                hx-target="#res-container"
                hx-vals='{{"p": "{p[1]}", "placeId": "{p[0]}"}}'
                hx-params="not q"
            >
                {p[1]}
            </button>
        """
        for p in predictions
    ]

    return Res(
        html=f"""
          <div
            id="starting_address_results"
            style="visibility: {"hidden" if len(htmlElements) == 0 else "visible"}"
          > {"".join(htmlElements)}
          </div>
        """
    )


def search_address(starting_address: str | None) -> list[tuple[str, str]]:
    if starting_address is None or starting_address.strip() == "":
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
            "X-Goog-Api-Key": settings.gmapsApiKey,
            "X-Goog-FieldMask": "suggestions.placePrediction.placeId,suggestions.placePrediction.text.text",
            "Content-Type": "application/json",
        },
    )

    if not res.ok:
        return []

    suggestions = res.json().get("suggestions")

    if suggestions is None:
        return []

    return [
        (sug["placePrediction"]["placeId"], sug["placePrediction"]["text"]["text"])
        for sug in suggestions
    ]


class Store(Req):
    important: str | None = None


@app.post("/api/store")
async def store_search(
    store: Store,
) -> Res:
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

    return Res(html="".join(htmlStores))


def search_store(store: str | None) -> pd.DataFrame:
    data = pd.read_csv("public/static/data/stores_location.csv")

    if not store or store.strip() == "":
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


@app.post("/api/setStartingAddress")
async def setStartingAddress(req: SetAddrModel) -> Res:
    p = req.p
    starting_address = p

    placeRes = requests.get(
        f"https://places.googleapis.com/v1/places/{req.placeId}",
        headers={
            "X-Goog-Api-Key": settings.gmapsApiKey,
            "X-Goog-FieldMask": "location",
            "Content-Type": "application/json",
        },
    )

    return Res(
        html=f"""
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
    """,
        data={"action": "setStartingAddress", "location": placeRes.json()["location"]},
    )


@app.get("/api/removeStartingAddress")
async def removeStartingAddress() -> Res:
    return Res(
        html="""
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
    """,
        data={"action": "removeStartingAddress"},
    )


@app.get("/test")
async def test() -> Res:
    return Res(
        html="""
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
          <span>asdf</span>
        </div>
    """,
        data={
            "starting_address": "asdf",
        },
    )
