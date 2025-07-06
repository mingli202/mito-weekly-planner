import json
import unittest
from pydantic import BaseModel
import math


class Location(BaseModel):
    no: int
    lat: float
    lng: float
    index: int


class Distance(BaseModel):
    no: int
    d: float


locations: list[Location] = []
with open("./public/static/data/locations-fixed.json") as file:
    locations = [
        Location(
            no=loc["No Mag."],
            lat=loc["latitude"],
            lng=loc["longitude"],
            index=loc["index"],
        )
        for loc in json.loads(file.read())
    ]

distances: dict[str, list[Distance]] = {}
with open("distances.json", "r") as file:
    _d = json.loads(file.read())

    for cur, dist in _d.items():
        _d[cur] = [Distance(no=__d["no"], d=__d["d"]) for __d in dist]

    distances = _d

home = Location(no=0, lat=45.461915521005885, lng=-73.87317833852978, index=0)


class Test(unittest.TestCase):
    def setUp(self) -> None:
        self.grid = [
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
        self.points = {}
        for i, row in enumerate(self.grid):
            for k, col in enumerate(row):
                if col > 0:
                    self.points.update({col: (i, k)})

        """
        {
            1: (0, 0),
            2: (1, 0),
        }
        """

        self.distances: dict[int, list[Distance]] = {}
        for cur, p_cur in self.points.items():
            self.distances[cur] = []
            for other, p_other in self.points.items():
                if cur == other:
                    continue

                dist = calc_distance(p_cur, p_other)
                self.distances[cur].append(Distance(no=other, d=dist))

            self.distances[cur].sort(key=lambda x: x.d)

        self.home = (3, 2)

    def test_generate_plans_normal(self):
        # every counter is spread apart and easy to guess what the user might want
        important: list[int] = [1, 13, 15, 8, 3]
        plans = [
            sorted(p) for p in generate_plans(self.distances, important, self.home)
        ]
        self.assertListEqual([[1, 2], [13, 14], [7, 15], [8, 16], [3, 4]], plans)

    def test_generate_close_important(self):
        important: list[int] = [1, 2, 19, 3, 4, 13]
        plans = [
            sorted(p) for p in generate_plans(self.distances, important, self.home)
        ]
        self.assertListEqual([[1, 2], [17, 19], [3, 4], [13, 14], [11, 20]], plans)

    def test_based_on_starting_pos(self):
        # should generate closest

        dist_from_home = {}
        for loc in locations:
            dist_from_home[loc.no] = calc_distance(
                (loc.lat, loc.lng), (home.lat, home.lng)
            )

        # self.assertEqual(
        #     [[8395, 8564], [517, 8367], [8247, 8316], [542, 8346], [8144, 8197]],
        #     generate_plans([]),
        # )

    def test_ltfive_important(self):
        pass

    def test_gtfive_important(self):
        pass

    def test_no_important(self):
        pass

    def test_gt_14_important(self):
        pass

    def test_distances(self):
        for val in distances.values():
            prev = -math.inf
            for store in val:
                self.assertTrue(store.d > prev)
                prev = store.d


def generate_plans(
    distances: dict[int, list[Distance]], importants: list[int], home: tuple[int, int]
) -> list[list[int]]:
    """
    Priority:
    1. Must go to all importants
    2. Minimum distance between stores in one day
    3. Minimize total distance travelled
    """
    out: list[list[int]] = []
    taken: set[int] = set()

    for i in importants:
        distancesToOtherSorted = distances[i]
        k = 0
        while distancesToOtherSorted[k].no in taken:
            k += 1

        out.append([i, distancesToOtherSorted[k].no])
        taken.add(distancesToOtherSorted[k].no)

    return out


def calc_distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def main():
    distances = {}

    for cur in locations:
        distances[cur.no] = []
        for other in locations:
            if cur.no == other.no:
                continue

            distances[cur.no].append(
                {
                    "no": other.no,
                    "d": calc_distance((cur.lat, cur.lng), (other.lat, other.lng)),
                }
            )

        distances[cur.no].sort(key=lambda d: d["d"])

    with open("distances.json", "w") as file:
        file.write(json.dumps(distances, indent=2))


if __name__ == "__main__":
    unittest.main()
