#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import geopy.distance
import math
import sqlite3

ANSI_UP_DEL = u"\u001b[F\u001b[K"

class C2GCalcTrips:
    def __init__(self):
        self.dbfile = "car2go.db3"
        self.conn = sqlite3.connect(self.dbfile)
        self.c = self.conn.cursor()
        self.c.execute("PRAGMA foreign_keys=on;")
        self.run()

    def run(self):
        all_cars = self.load_cars()
        print("Clearing table.")
        self.c.execute("DELETE FROM trips;")
        print("Going to analyse {} cars.".format(len(all_cars)))
        inserter = self.conn.cursor()
        num_trips = 0
        cars_done = 0
        for carId in all_cars:
            is_occupied = False
            self.c.execute("SELECT stamp, occupied, fuel, latitude, longitude FROM car_state WHERE carId=? ORDER BY stamp ASC;", (carId,))
            for row in self.c:
                if row[1] == 1:
                    is_occupied = True
                    occu_state = row
                elif row[1] == 0 and is_occupied:
                    is_occupied = False
                    seconds = row[0] - occu_state[0]
                    minutes = seconds / 60
                    if seconds <= 70:
                        # probably a glitch
                        continue
                    price = math.ceil(minutes) * all_cars[carId]
                    old_spot = (occu_state[3], occu_state[4])
                    new_spot = (row[3], row[4])
                    distance = geopy.distance.distance(old_spot, new_spot).kilometers
                    dataset = (
                        carId,
                        occu_state[0],
                        row[0],
                        minutes,
                        distance,
                        (occu_state[2] - row[2]),
                        price
                    )
                    #print(repr(dataset))
                    inserter.execute("INSERT INTO trips (carId, stamp_departure, stamp_arrival, duration_minutes, distance_km, fuel_spent, price) VALUES (?,?,?,?,?,?,?);", dataset)
                    num_trips += 1
            cars_done += 1
            print("{}/{} cars done. {} trips found.".format(cars_done, len(all_cars), num_trips))
            if cars_done < len(all_cars):
                print(ANSI_UP_DEL, end="")
        print("")

        self.conn.commit()
        self.c.execute("VACUUM;")
        self.conn.close()

    def load_cars(self):
        print("Loading known cars from database.")
        self.c.execute("SELECT c.carId, c.plate, cm.pricePerMinute FROM cars c LEFT JOIN car_models cm ON c.vinPrefix=cm.vinPrefix;")
        result = {}
        for row in self.c.fetchall():
            result[row[0]] = row[2]
        return result

if __name__=="__main__":
    C2GCalcTrips()
