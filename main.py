import json
import re
from datetime import datetime

import pandas as pd
import requests
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic_settings import BaseSettings, SettingsConfigDict

from data import load_locations
from models import Location, Req, Res, SetAddrModel, StoreInfo
from storeSchedule import make_schedule

StaticFiles.is_not_modified = lambda self, *args, **kwargs: False


class Settings(BaseSettings):
    gmapsApiKey: str = ""
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
app = FastAPI(
    title="Mito Weekly Planner",
    description="App that lets you efficiently plan out which stores to go based on your location and urgency of visits.",
)


app.mount("/static", StaticFiles(directory="public/static"), name="static")

data = pd.read_csv("public/static/data/stores_location.csv")

middle_of_montreal = Location(
    no=0, lat=45.51694470739976, lng=-73.72324462099256, index=0
)


class State:
    home: Location = middle_of_montreal


state = State()
locations: list[Location] = load_locations()


@app.get("/")
async def root():
    return FileResponse("public/static/index.html")


@app.get("/api/googleScript")
async def googleScript():
    return HTMLResponse(
        content="""
    <script src="/static/js/module.js" type="module" defer></script>
    <script>
      ((g) => {
        var h,
          a,
          k,
          p = "The Google Maps JavaScript API",
          c = "google",
          l = "importLibrary",
          q = "__ib__",
          m = document,
          b = window;
        b = b[c] || (b[c] = {});
        var d = b.maps || (b.maps = {}),
          r = new Set(),
          e = new URLSearchParams(),
          u = () =>
            h ||
            (h = new Promise(async (f, n) => {
              await (a = m.createElement("script"));
              e.set("libraries", [...r] + "");
              for (k in g)
                e.set(
                  k.replace(/[A-Z]/g, (t) => "_" + t[0].toLowerCase()),
                  g[k],
                );
              e.set("callback", c + ".maps." + q);
              a.src = `https://maps.${c}apis.com/maps/api/js?` + e;
              d[q] = f;
              a.onerror = () => (h = n(Error(p + " could not load.")));
              a.nonce = m.querySelector("script[nonce]")?.nonce || "";
              m.head.append(a);
            }));
        d[l]
          ? console.warn(p + " only loads once. Ignoring:", g)
          : (d[l] = (f, ...n) => r.add(f) && u().then(() => d[l](f, ...n)));
      })({"""
        + f'key: "{settings.gmapsApiKey}",'
        + """
        v: "quarterly",
        // Use the 'v' parameter to indicate the version to use (weekly, beta, alpha, etc.).
        // Add other bootstrap parameters as needed, using camel case.
      });
    </script>
    """
    )


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


@app.get("/api/store/{id}")
async def store_info(id: int) -> StoreInfo:
    store = data.loc[data["No Mag."] == id].to_numpy()[0]

    return StoreInfo(
        number=store[0],
        name=store[1],
        addr=store[2],
        city=store[3],
        postalCode=store[4],
    )


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
                    <button
                        hx-post="/api/store/location"
                        type="button"
                        hx-vals='{{"q": "{stores.loc[i]["No Mag."]}", "action": "setCenter"}}'
                        hx-ext="json-enc"
                    >#{stores.loc[i]["No Mag."]}</button>
                    <div class="store-card-must-visit">
                        <label for="store{stores.loc[i]["No Mag."]}">Urgent</label>
                        <input
                            type="checkbox"
                            id="store{stores.loc[i]["No Mag."]}"
                            onchange="toggleImportant({stores.loc[i]["No Mag."]})" 
                            {"checked" if stores.loc[i]["No Mag."] in important else ""} 
                        />
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
    # data = pd.read_csv("public/static/data/stores_location.csv")

    if not store or store.strip() == "":
        return data

    return data.loc[
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


@app.post("/api/setStartingAddress")
async def setStartingAddress(req: SetAddrModel) -> Res:
    p = req.p

    placeRes = requests.get(
        f"https://places.googleapis.com/v1/places/{req.placeId}",
        headers={
            "X-Goog-Api-Key": settings.gmapsApiKey,
            "X-Goog-FieldMask": "location",
            "Content-Type": "application/json",
        },
    )

    location = placeRes.json()["location"]
    state.home = Location(
        no=0, index=-1, lat=location["latitude"], lng=location["longitude"]
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
        data={"action": "setStartingAddress", "location": location},
    )


@app.get("/api/removeStartingAddress")
async def removeStartingAddress() -> Res:
    state.home = middle_of_montreal

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


@app.post("/api/store/location")
async def location(req: Req) -> Res:
    if not req.q:
        return Res()

    no = req.q

    left = 0
    right = locations.__len__() - 1
    middle = (left + right) // 2

    while left <= right:
        middle = (left + right) // 2

        if int(no) < locations[middle].no:
            right = middle - 1
        elif int(no) > locations[middle].no:
            left = middle + 1
        else:
            break

    return Res(data={"action": req.action, "location": locations[middle].model_dump()})


@app.post("/api/generate")
async def generate(store: Store) -> Res:
    important: list[str] = []

    if store.important:
        important = list(map(str, json.loads(store.important)))

    schedules = make_schedule(state.home, locations, important)

    days = ["monday", "tuesday", "wednesday", "thursday", "friday"]

    now = datetime.now().timestamp()

    html = [
        f"""
        <div class="schedule-container" onclick="showSchedule({
            [day[0] for day in schedule[0]]
        }, 'schedule-{i}-{now}')" id="schedule-{i}-{now}">
          <p>Plan {i + 1} (~{round(schedule[1])}km)</p>
          <div style="display: flex; gap: 0.5rem">
            {
            "".join(
                f'''
                <div class="{days[k]} day">
                    {"".join(f"<p>#{d}</p>" for d in day[0])}
                    <p>{round(day[1])}km</p>
                </div>
            '''
                for k, day in enumerate(schedule[0])
            )
        }
          </div>
        </div>
        """
        for i, schedule in enumerate(schedules)
    ]

    return Res(html="".join(html))
