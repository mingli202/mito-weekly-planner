import re
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
import pandas as pd

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


@app.get("/store")
async def store_search(q: str | None = None):
    stores = search_store(q)

    htmlStores = [
        f"""
            <div class="store-card">
                <div class="store-header">
                    <h3>#{stores.loc[i]["No Mag."]}</h3>
                    <div class="store-card-must-visit">
                        <label for="store{stores.loc[i]["No Mag."]}">Must visit</label>
                        <input type="checkbox" id="store{stores.loc[i]["No Mag."]}" />
                    </div>
                </div>
                <p class="store-card-info">{stores.loc[i]["Nom Mag."]}</p>
                <p class="store-card-info">{stores.loc[i]["Adresse Mag."]}, {stores.loc[i]["Ville"]}, {stores.loc[i]["Postal"]}</p>
            </div>
        """
        for i in stores.index
    ]

    return HTMLResponse("\n".join(htmlStores))


def search_address(starting_address: str) -> JSONResponse:
    return JSONResponse({"address": "hellow orld"})


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
