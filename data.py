import json
import pandas as pd
import requests
import os

data = pd.read_csv("public/static/stores_location.csv")

locations = []

if os.path.exists("public/static/data/locations.json"):
    print("already exist")
else:
    for i in data.index:
        store = data.loc[i]

        addr = ", ".join([store["Adresse Mag."], store["Ville"], store["Postal"]])

        url = "https://places.googleapis.com/v1/places:searchText"

        req = requests.post(
            url,
            json={
                "textQuery": addr,
                "locationBias": {
                    "circle": {
                        "center": {
                            "latitude": 45.508640423914336,
                            "longitude": -73.63476131464701,
                        },
                        "radius": 50_000,
                    }
                },
            },
            headers={
                "X-Goog-Api-Key": "AIzaSyCQrnHYiPKBQO0ImU926iIECNkzH3Pp92g",
                "X-Goog-FieldMask": "places.location",
            },
        )

        places = req.json()["places"]
        if len(places) > 1:
            print(addr)

        locations.append(places[0]["location"])

    with open("locations.json", "w") as file:
        file.write(json.dumps(locations, indent=2))


"""
451, 254 Rue Hôtel-De-Ville CP483, Rivière Du Loup, G5R 1M4
8223, 30 Maple RR1, Grenville, J0V 1J0
8542, 81 Chemin Lavaltrie, Lavaltrie, J5T 2H5
8569, 3950 King Street Ouest, Sherbrooke, J1L 1P6
8586, 580 Rue Victoria, 45 rue Daigle, E3V 1L8
"""
not_uniques = [
    "254 Rue Hôtel-De-Ville CP483",
    "30 Maple RR1",
    "81 Chemin Lavaltrie",
    "3950 King Street Ouest",
    "580 Rue Victoria",
]
print(data.loc[data["Adresse Mag."].isin(not_uniques)])


def loc(lat, lng):
    return {"latitude": lat, "longitude": lng}


with open("public/static/data/locations.json", "r") as file:
    locations = json.loads(file.read())
    print(locations[150])

    locations[17] = loc(47.8253313612993, -69.55423773112572)
    locations[77] = loc(45.623092963992306, -74.59373800238156)
    locations[138] = loc(45.89208793398586, -73.29560871401394)
    locations[146] = loc(45.38786262688279, -71.95798818282371)
    locations[150] = loc(47.38232469398187, -68.33797471729301)

with open("public/static/data/locations-fixed.json", "w") as file:
    file.write(json.dumps(locations, indent=2))
