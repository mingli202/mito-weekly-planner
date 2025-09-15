from typing import OrderedDict
import math

from models import Location
from data import load_locations
import json
import os
import itertools
from copy import deepcopy
from collections import deque

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
) -> tuple[dict[str, OrderedDict[str, float]], OrderedDict[str, float]]:
    pairwise_distances: dict[str, OrderedDict[str, float]] = dict()
    distances_from_home: OrderedDict[str, float] = OrderedDict()

    if os.path.exists("./public/static/data/pairwise_distances.json"):
        with open("./public/static/data/pairwise_distances.json") as file:
            pairwise_distances = json.load(file)

        for i, l1 in enumerate(locations):
            distances_from_home[str(l1.no)] = haversine_km(l1, home)
    else:
        for i, l1 in enumerate(locations):
            for j, l2 in enumerate(locations[i + 1 :]):
                if i == j:
                    continue
                dist = haversine_km(l1, l2)

                if l1.no not in pairwise_distances:
                    pairwise_distances[str(l1.no)] = OrderedDict()

                if l2.no not in pairwise_distances:
                    pairwise_distances[str(l2.no)] = OrderedDict()

                pairwise_distances[str(l1.no)][str(l2.no)] = dist
                pairwise_distances[str(l2.no)][str(l1.no)] = dist

            distances_from_home[str(l1.no)] = haversine_km(l1, home)

            pairwise_distances[str(l1.no)] = OrderedDict(
                sorted(pairwise_distances[str(l1.no)].items(), key=lambda x: x[1])
            )

        with open("./public/static/data/pairwise_distances.json", "w") as file:
            json.dump(pairwise_distances, file, indent=2, ensure_ascii=True)

    distances_from_home = OrderedDict(
        sorted(distances_from_home.items(), key=lambda x: x[1])
    )

    return pairwise_distances, distances_from_home


def placeholder_distances() -> tuple[
    dict[str, OrderedDict[str, float]], OrderedDict[str, float]
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

    pairwise_distances: dict[str, OrderedDict[str, float]] = {}
    distances_from_home: OrderedDict[str, float] = OrderedDict()

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

            if str(cur) not in pairwise_distances:
                pairwise_distances[str(cur)] = OrderedDict()

            if str(other) not in pairwise_distances:
                pairwise_distances[str(other)] = OrderedDict()

            pairwise_distances[str(cur)][str(other)] = dist
            pairwise_distances[str(other)][str(cur)] = dist

        pairwise_distances[str(cur)] = OrderedDict(
            sorted(pairwise_distances[str(cur)].items(), key=lambda x: int(x[1]))
        )

        distances_from_home[str(cur)] = math.sqrt(
            (home[1] - p_cur[1]) ** 2 + (home[0] - p_cur[0]) ** 2
        )

    distances_from_home = OrderedDict(
        sorted(distances_from_home.items(), key=lambda x: int(x[1]))
    )

    return pairwise_distances, distances_from_home


def make_schedule(
    home: Location,
    locations: list[Location],
    important_locations: list[str],
    test: bool = False,
) -> list[tuple[list[list[str]], float, float]]:
    if test:
        pairwise_distances, distances_from_home = placeholder_distances()
        important_locations = list(map(str, [1, 2]))
    else:
        pairwise_distances, distances_from_home = compute_distances(home, locations)

    candidate_schedules: deque[list[list[str]]] = deque()
    schedules: list[tuple[list[list[str]], float, float]] = []
    already_seen: set[str] = set()

    def to_str(candidate: list[list[str]]) -> str:
        return str(
            sorted(
                [sorted(day) for day in candidate if len(day) > 0],
                key=lambda x: x[0],
            )
        )

    def compute_closesest(
        candidate: list[list[str]], ordered_distances: OrderedDict[str, float]
    ) -> str:
        closest_stores = list(ordered_distances.keys())

        k = 0
        closest_from_last_store = closest_stores[k]

        scheduled_stores = set(itertools.chain.from_iterable(candidate))

        while closest_from_last_store in scheduled_stores:
            add_candidate(candidate, i, closest_from_last_store)

            k += 1
            closest_from_last_store = closest_stores[k]

        return closest_from_last_store

    def add_candidate(candidate: list[list[str]], i: int, closest_from_last_store: str):
        another_candidate = deepcopy(candidate)

        for dayy in another_candidate:
            if closest_from_last_store in dayy:
                dayy.remove(closest_from_last_store)
                break

        another_candidate[i].append(closest_from_last_store)

        another_candidate_str = to_str(another_candidate)
        if another_candidate_str in already_seen:
            return

        candidate_schedules.append(another_candidate)

    candidate_schedules.append([])

    while len(candidate_schedules) > 0:
        candidate = candidate_schedules.popleft()

        if to_str(candidate) in already_seen:
            continue

        is_candidate_full = False
        i = 0

        while not is_candidate_full:
            if len(candidate) <= i:
                candidate.append([])

            day = candidate[i]
            already_seen.add(to_str(candidate))

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
                    candidate, pairwise_distances[str(last_store)]
                )

                day.append(closest_from_last_store)

            is_candidate_full = len(candidate) == DAYS_IN_WEEK and all(
                len(day) >= 2 for day in candidate
            )

            i = (i + 1) % DAYS_IN_WEEK

        if to_str(candidate) in already_seen:
            continue
        else:
            already_seen.add(to_str(candidate))

        # penalize for long pairwise distances
        # not very important for distance from home
        weight = 0
        total_distance = 0
        for day in candidate:
            weight += (
                sum(
                    pow(pairwise_distances[day[i]][day[i + 1]], 3)
                    for i in range(len(day) - 1)
                )
                + distances_from_home[day[0]] / 2
                + distances_from_home[day[-1]] / 2
            )
            day.sort()

            total_distance += (
                sum(pairwise_distances[day[i]][day[i + 1]] for i in range(len(day) - 1))
                + distances_from_home[day[0]]
                + distances_from_home[day[-1]]
            )

        schedules.append(
            (sorted(candidate, key=lambda x: x[0]), total_distance, weight)
        )

    return sorted(schedules, key=lambda x: x[2])


def main():
    locations = load_locations()

    home = Location(no=0, lat=45.461915521005885, lng=-73.87317833852978, index=0)
    important_locations = list(map(str, [110, 8793, 8293]))

    schedules = make_schedule(home, locations, important_locations)

    print(len(schedules))
    print("\n".join(map(json.dumps, schedules[:10])))


if __name__ == "__main__":
    main()
