from typing import OrderedDict
import math

from models import Location
from data import load_locations
import json
import os
import itertools
from copy import deepcopy

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


def point_distance(p1: tuple[float, float], p2: tuple[float, float]) -> float:
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


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

    distances_from_home = OrderedDict(
        sorted(distances_from_home.items(), key=lambda x: x[1])
    )

    return pairwise_distances, distances_from_home


def make_schedule(
    home: Location, locations: list[Location], important_locations: list[int]
) -> list[tuple[list[list[int]], float]]:
    # pairwise_distances, distances_from_home = compute_distances(home, locations)
    pairwise_distances, distances_from_home = placeholder_distances()

    candidate_schedules: list[list[list[int]]] = [[]]
    schedules: list[tuple[list[list[int]], float]] = []

    pairs: set[tuple[int, ...]] = set()

    def compute_closesest(
        candidate: list[list[int]], ordered_distances: OrderedDict[int, float]
    ) -> int:
        closest_stores = list(ordered_distances.keys())

        k = 0
        closest_from_last_store = closest_stores[k]

        scheduled_stores = set(itertools.chain.from_iterable(candidate))

        while closest_from_last_store in scheduled_stores:
            add_candidate(candidate, i, closest_from_last_store)

            k += 1
            closest_from_last_store = closest_stores[k]

        return closest_from_last_store

    def add_candidate(candidate: list[list[int]], i: int, closest_from_last_store: int):
        another_candidate = deepcopy(candidate)

        day_copy = deepcopy(another_candidate[i])
        day_copy.append(closest_from_last_store)
        day_copy.sort()
        if tuple(day_copy) in pairs:
            return

        for dayy in another_candidate:
            if closest_from_last_store in dayy:
                dayy.remove(closest_from_last_store)
                break

        another_candidate[i].append(closest_from_last_store)

        pairs.add(tuple(day_copy))

        candidate_schedules.append(another_candidate)

    while len(candidate_schedules) > 0:
        candidate = candidate_schedules.pop()
        is_candidate_full = False
        i = 0

        while not is_candidate_full:
            if len(candidate) <= i:
                candidate.append([])

            day = candidate[i]

            if len(day) == 0:
                if len(important_locations) > 0:
                    important = important_locations.pop()
                    day.append(important)
                else:
                    closest_from_home = compute_closesest(
                        candidate, distances_from_home
                    )
                    day.append(closest_from_home)
            elif len(day) == 1:
                last_store = day[-1]

                closest_from_last_store = compute_closesest(
                    candidate, pairwise_distances[last_store]
                )

                day.append(closest_from_last_store)

            pairs.add(tuple(day))
            is_candidate_full = all(len(day) >= 2 for day in candidate)

            i = (i + 1) % DAYS_IN_WEEK

        total_distance = 0
        for day in candidate:
            total_distance += (
                sum(
                    pow(pairwise_distances[day[i]][day[i + 1]], 2)
                    for i in range(len(day) - 1)
                )
                + distances_from_home[day[0]]
                + distances_from_home[day[-1]]
            )

        schedules.append((candidate, total_distance))

    return sorted(schedules, key=lambda x: x[1])


def main():
    locations = load_locations()

    home = Location(no=0, lat=45.461915521005885, lng=-73.87317833852978, index=0)
    important_locations = [1, 2]

    schedules = make_schedule(home, locations, important_locations)

    print("\n".join(map(json.dumps, schedules)))


if __name__ == "__main__":
    main()
