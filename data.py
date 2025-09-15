import json
import pandas as pd
import requests
import os
from dotenv import load_dotenv

from models import Location

load_dotenv()


def compute_locations():
    data = pd.read_csv("public/static/data/stores_location.csv")

    locations = []

    if os.path.exists("public/static/data/locations.json"):
        print("already exist")
        return
    for i in data.index:
        store = data.loc[i]

        addr = ", ".join([store["Adresse Mag."], store["Ville"], store["Postal"]])

        url = "https://places.googleapis.com/v1/places:searchText"

        req = requests.post(
            url,
            json={
                "textQuery": addr,
            },
            headers={
                "X-Goog-Api-Key": os.getenv("gmapsApiKey"),
                "X-Goog-FieldMask": "places.location",
            },
        )

        places = req.json()["places"]
        if len(places) > 1:
            print(i, store["No Mag."], addr)

        lo = places[0]["location"]
        lo["No Mag."] = str(store["No Mag."])
        lo["index"] = i

        locations.append(lo)

    with open("public/static/data/locations.json", "w") as file:
        json.dump(locations, file, indent=2)

    """
    17 451, 254 Rue Hôtel-De-Ville CP483, Rivière Du Loup, G5R 1M4
    77 8223, 30 Maple RR1, Grenville, J0V 1J0
    138 8542, 81 Chemin Lavaltrie, Lavaltrie, J5T 2H5
    146 8569, 3950 King Street Ouest, Sherbrooke, J1L 1P6
    150 8586, 580 Rue Victoria, 45 rue Daigle, E3V 1L8

    43 8046 265 Child, Coaticook, J1A 2B5
    74 8214 299 Boul. Laurier, St-Lambert, J4R 2L1
    99 8316 490  28ème Avenue, Lachine, H8S 3Z4
    """


def fix_locations():
    if os.path.exists("public/static/data/locations-fixed.json"):
        print("already exist")
        return

    def loc(lat, lng, d):
        return {
            "No Mag.": d["No Mag."],
            "index": d["index"],
            "latitude": lat,
            "longitude": lng,
        }

    with open("public/static/data/locations.json", "r") as file:
        locations = json.loads(file.read())

        locations[17] = loc(47.8253313612993, -69.55423773112572, locations[17])
        locations[43] = loc(45.13603191049802, -71.80524055528183, locations[43])
        locations[74] = loc(45.49362880858445, -73.50159030238679, locations[74])
        locations[77] = loc(45.623092963992306, -74.59373800238156, locations[77])
        locations[99] = loc(45.437422536064055, -73.68758645751039, locations[99])
        locations[138] = loc(45.89208793398586, -73.29560871401394, locations[138])
        locations[146] = loc(45.38786262688279, -71.95798818282371, locations[146])
        locations[150] = loc(47.38232469398187, -68.33797471729301, locations[150])

    with open("public/static/data/locations-fixed.json", "w") as file:
        json.dump(locations, file, indent=2)


def load_locations() -> list[Location]:
    locations: list[Location] = []
    with open("./public/static/data/locations-fixed.json") as file:
        locations = [
            Location(
                no=loc["No Mag."],
                lat=loc["latitude"],
                lng=loc["longitude"],
                index=loc["index"],
            )
            for loc in json.load(file)
        ]

    return locations
