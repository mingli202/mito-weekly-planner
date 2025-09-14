from typing import OrderedDict
import math

from models import Location
from data import load_locations
import json
import os

DAYS_IN_WEEK = 5


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

    if os.path.exists("./public/static/data/pairwise_distances.json"):
        with open("./public/static/data/pairwise_distances.json") as file:
            pairwise_distances = json.load(file)

        for i, l1 in enumerate(locations[:-1]):
            distances_from_home[l1.no] = haversine_km(l1, home)
    else:
        for i, l1 in enumerate(locations):
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

        with open("./public/static/data/pairwise_distances.json", "w") as file:
            json.dump(pairwise_distances, file, indent=2)

    distances_from_home = OrderedDict(
        sorted(distances_from_home.items(), key=lambda x: x[1])
    )

    return pairwise_distances, distances_from_home


def placeholder_distances() -> tuple[
    dict[int, OrderedDict[int, float]], OrderedDict[int, float]
]:
    grid = [
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 12],
        [2, 0, 0, 0, 0, 11, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 10, 0, 0],
        [0, 0, -1, 0, 0, 20, 0, 0, 9, 0],
        [0, 0, 19, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 16, 0, 0],
        [0, 0, 4, 0, 17, 0, 8, 0, 0, 0],
        [0, 3, 0, 0, 0, 0, 7, 15, 0, 0],
        [0, 0, 0, 0, 5, 0, 0, 0, 0, 13],
        [18, 0, 6, 0, 0, 0, 0, 0, 14, 0],
    ]
    home = (3, 2)

    pairwise_distances: dict[int, OrderedDict[int, float]] = {}
    distances_from_home: OrderedDict[int, float] = OrderedDict()

    points: dict[int, tuple[int, int]] = {}
    for i, row in enumerate(grid):
        for k, col in enumerate(row):
            if col > 0:
                points.update({col: (i, k)})

    pts = list(points.items())
    for i, (cur, p_cur) in enumerate(pts):
        for other, p_other in pts[i + 1 :]:
            dist = math.sqrt(
                (p_cur[1] - p_other[1]) ** 2 + (p_cur[0] - p_other[0]) ** 2
            )

            if cur not in pairwise_distances:
                pairwise_distances[cur] = OrderedDict()

            if other not in pairwise_distances:
                pairwise_distances[other] = OrderedDict()

            pairwise_distances[cur][other] = dist
            pairwise_distances[other][cur] = dist

        pairwise_distances[cur] = OrderedDict(
            sorted(pairwise_distances[cur].items(), key=lambda x: x[1])
        )

        distances_from_home[cur] = math.sqrt(
            (home[1] - p_cur[1]) ** 2 + (home[0] - p_cur[0]) ** 2
        )

    return pairwise_distances, distances_from_home


def make_schedule(
    home: Location, locations: list[Location], important_locations: list[int]
) -> list[list[list[int]]]:
    # pairwise_distances, distances_from_home = compute_distances(home, locations)
    pairwise_distances, distances_from_home = placeholder_distances()

    candidate_schedules: list[list[list[int]]] = [[]]

    i = 0
    are_all_candidates_full = False
    while not are_all_candidates_full:
        are_all_candidates_full = True

        for candidate in candidate_schedules:
            if len(candidate) <= i:
                candidate.append([])

            day = candidate[i]

            if len(day) == 0:
                if important := important_locations.pop():
                    day.append(important)
                else:
                    closest_from_home = list(distances_from_home.keys())[0]
                    day.append(closest_from_home)
            else:
                last_store = day[-1]
                closest_from_last_store = list(pairwise_distances[last_store].keys())[0]
                day.append(closest_from_last_store)

            if any(len(day) != 2 for day in candidate):
                are_all_candidates_full = False

        i = (i + 1) % DAYS_IN_WEEK

    return candidate_schedules


def main():
    locations = load_locations()

    home = Location(no=0, lat=45.461915521005885, lng=-73.87317833852978, index=0)
    important_locations = [1, 18, 14, 12, 17]

    schedules = make_schedule(home, locations, important_locations)

    print(f"schedules: {schedules}")


if __name__ == "__main__":
    main()
