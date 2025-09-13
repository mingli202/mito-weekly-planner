from typing import OrderedDict
from pydantic import BaseModel
import json
import math


class Location(BaseModel):
    no: int
    lat: float
    lng: float
    index: int


class Distance(BaseModel):
    no: int
    d: float


def haversine_km(l1: Location, l2: Location):
    lat1, lon1 = l1.lat, l1.lng
    lat2, lon2 = l2.lat, l2.lng
    radius = 6371  # km of earth
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = pow(math.sin(dlat / 2), 2) + math.cos(math.radians(lat1)) * math.cos(
        math.radians(lat2)
    ) * pow(math.sin(dlon / 2), 2)
    d = 2 * radius * math.asin(math.sqrt(a))
    return d


def compute_distances(
    home: Location, locations: list[Location]
) -> tuple[dict[int, OrderedDict[int, float]], OrderedDict[int, float]]:
    pairwise_distances: dict[int, OrderedDict[int, float]] = dict()
    distances_from_home: OrderedDict[int, float] = OrderedDict()

    for i, l1 in enumerate(locations[:-1]):
        for j, l2 in enumerate(locations[i + 1 :]):
            if i == j:
                continue
            dist = haversine_km(l1, l2)

            if l1.no not in pairwise_distances:
                pairwise_distances[l1.no] = OrderedDict()

            if l2.no not in pairwise_distances:
                pairwise_distances[l2.no] = OrderedDict()

            pairwise_distances[l1.no][l2.no] = dist
            pairwise_distances[l2.no][l1.no] = dist

        distances_from_home[l1.no] = haversine_km(l1, home)

        pairwise_distances[l1.no] = OrderedDict(
            sorted(pairwise_distances[l1.no].items(), key=lambda x: x[1])
        )

    distances_from_home = OrderedDict(
        sorted(distances_from_home.items(), key=lambda x: x[1])
    )

    return pairwise_distances, distances_from_home


def main():
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

    home = Location(no=0, lat=45.461915521005885, lng=-73.87317833852978, index=0)
    pairwise_distances, distances_from_home = compute_distances(home, locations)
    print(pairwise_distances)
    print(distances_from_home)


if __name__ == "__main__":
    main()
