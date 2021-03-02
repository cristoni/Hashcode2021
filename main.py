import os, sys
from multiprocessing import Process

# DURATION: int = 0
# INTERSECTIONS = None
# STREETS = None

class Car:
    path: list[str]
    position: str
    queued: bool
    time_to_light: int
    last_move_clock_time: int
    score: float

    def __init__(self, path, position):
        self.path = path
        self.position = position
        self.queued = True
        self.time_to_light = 0
        self.last_move_clock_time = 0
        self.score = 0

    def update_score(self, queue_position):
        global DURATION
        residual_path = Street.get_path_length(self.path[self.path.index(self.position)+1:])
        self.score = max(0, DURATION - (queue_position + residual_path)) / (len(self.path) - self.path.index(self.position))

class Street:
    name: str
    l: int
    light: bool
    ti: int
    cars: list[Car]

    def __init__(self, name, l, light = False, ti = 0):
        self.name = name
        self.l = l
        self.light = light
        self.ti = ti
        self.cars = []

    @staticmethod
    def get_path_length(path: list[str]):
        return sum(STREETS[name].l for name in path)

class Intersection:
    id: int
    in_streets: list[str]
    out_streets: list[str]
    schedule: list[str]

    def __init__(self, id, in_streets, out_streets):
        self.id = id
        self.in_streets = in_streets
        self.out_streets = out_streets
        self.schedule = []

    @staticmethod
    def lifecicle():
        # Devo fare un controllo sui semafori prima dell'inizio del giro per determinare
        # lo stato iniziale di tutti i semafori
        for k, intersection in INTERSECTIONS.items():
                for street in intersection.in_streets:
                    for i, car in enumerate(STREETS[street].cars):
                        car.update_score(i)

                # print("Intersezione ", intersection.id, ": ", STREETS[intersection.get_highest_scoring_street()].name, " - ", intersection.get_score())
                if intersection.get_score() <= 0:
                    continue
                
                highest_scoring_street = intersection.get_highest_scoring_street()
                for street in intersection.in_streets:
                    if street == highest_scoring_street:
                        STREETS[street].light = True
                        if len(intersection.schedule) > 0 and intersection.schedule[len(intersection.schedule) - 1] == street:
                            STREETS[street].ti += 1
                        else:
                            if street not in intersection.schedule:
                                STREETS[street].ti = 1
                                intersection.schedule.append(street)
                    else:
                        STREETS[street].light = False

    def output(self) -> str:
        output_streets = []
        for name in self.schedule:
            output_streets.append("{0} {1}".format(name, STREETS[name].ti))

        # print(output_streets)

        return "{0}\n{1}\n{2}\n".format(self.id, len(self.schedule), "\n".join(output_streets))
    
    def get_all_scores(self):
        return [sum(car.score for car in STREETS[name].cars) for name in self.in_streets]

    def get_score(self):
        scores = self.get_all_scores()
        return max(scores)

    def get_highest_scoring_street_index(self):
        scores = self.get_all_scores()
        return scores.index(max(scores))

    def get_highest_scoring_street(self):
        scores = self.get_all_scores()
        return self.in_streets[scores.index(max(scores))]

def city_from_file(path: str) -> tuple[dict[int, Intersection], dict[str, Street]]:
    intersections: dict[int, Intersection] = {}
    streets: dict[int, Street] = {}

    with open(path, 'r') as f:
        lines = f.read().splitlines()
        duration, I, S, V, F = lines[0].split(' ')

        for line in lines[1: int(S) + 1]:
            B, E, name, L = line.split(' ')
            B = int(B)
            E = int(E)
            streets[name] = Street(name, int(L))

            if B in intersections.keys():
                intersections[B].out_streets.append(name)
            else:                
                intersections[B] = Intersection(B, [], [name])

            if E in intersections.keys():
                intersections[E].in_streets.append(name)
            else:                
                intersections[E] = Intersection(E, [name], [])

        for line in lines[int(S) + 1:]:
            car_data = line.split(' ')
            starting_position = car_data[1]
            streets[starting_position].cars.append(Car(car_data[1:], starting_position))

        return int(duration), intersections, streets

def solve():
    global DURATION

    Intersection.lifecicle()
    
    # print("\n\n")

    while DURATION > 0:
        # print("clock: ", DURATION)
        # per ogni clock per macchina che non è ferma ad un semaforo questa deve avanzare
        for k, street in STREETS.items():
            # print("Strada in esame: ", street.name)
            for i in list(reversed(range(0, len(street.cars)))):
                # print(i, ": ", street.cars[i].position, " - ", street.cars[i].time_to_light)
                if street.cars[i].last_move_clock_time != DURATION:
                    street.cars[i].last_move_clock_time = DURATION

                    if street.cars[i].queued:
                        if street.light and i == 0:
                            # passa alla strada successiva
                            if street.cars[i].path.index(street.name) < len(street.cars[i].path) - 1:
                                # print("macchina cambia strada")
                                street.cars[i].queued = False
                                street.cars[i].time_to_light = STREETS[street.cars[i].path[street.cars[i].path.index(street.name) + 1]].l
                                street.cars[i].position = STREETS[street.cars[i].path[street.cars[i].path.index(street.name) + 1]].name
                                street.cars[i].score = 0
                                STREETS[street.cars[i].path[street.cars[i].path.index(street.name) + 1]].cars.append(street.cars[i])
                            # slitta la lista in avanti di uno
                            street.cars.pop(0)
                        else:
                            street.cars[i].update_score(i)
                            # print(street.cars[i].score)
                    else:
                        # print("l'auto avanza")
                        street.cars[i].time_to_light -= 1
                        if street.cars[i].time_to_light == 0:
                            # print("l'auto arriva al semaforo")
                            street.cars[i].queued = True
                            street.cars[i].update_score(i)
                            # print(street.cars[i].score)

                            if street.cars[i].path.index(street.name) == len(street.cars[i].path) - 1:
                                # print("l'auto è arrivata a destinazione")
                                street.cars.pop(i)

        # print("\n")

        Intersection.lifecicle()

        # print("\n\n")
        DURATION -= 1

    return [k for k, intersection in INTERSECTIONS.items() if len(intersection.schedule) > 0]

def main(input):
    global DURATION, INTERSECTIONS, STREETS
    DURATION, INTERSECTIONS, STREETS = city_from_file(input)

    # funzione per risolvere i nostri problemi di vita
    intersezioni_in_uso = solve()

    with open(input + ".out", "a") as f:
        f.write(str(len(intersezioni_in_uso)) + "\n")

        for id in intersezioni_in_uso:
            f.write(INTERSECTIONS[id].output())

if __name__ == '__main__':
    directory = r'.'
    for entry in os.scandir(directory):
        if (entry.path.endswith(".txt")
                and not entry.path.endswith(".out")) and entry.is_file():

            p = Process(target=main, args=(entry.name,))
            p.start()