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
    return FileResponse("./public/static/index.html")


@app.get("/search")
async def search(q: str | None = None):
    if q and q != "":
        return search_address(q)

    return HTMLResponse("")


@app.get("/store")
async def store_search(q: str | None = None):
    stores = search_store(q)
    print(stores)

    return HTMLResponse("")


def search_address(starting_address: str) -> JSONResponse:
    return JSONResponse({"address": "hellow orld"})


def search_store(store: str | None) -> pd.DataFrame:
    data = pd.read_csv("./public/stores_location.csv")

    if not store or store == "":
        return data

    data = data.loc[
        [
            all(
                any(
                    re.search(_store, s, re.I) is not None
                    for s in [
                        str(d["No Mag."]),
                        d["Nom Mag."],
                        d["Adresse Mag."],
                        d["Ville"],
                        d["Postal"],
                    ]
                )
                for _store in store.split(" ")
            )
            for d in [data.loc[i] for i in data.index]
        ]
    ]

    return data
