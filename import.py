#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import glob
import json
import math
import os
import re
import sqlite3

ANSI_UP_DEL = u"\u001b[F\u001b[K"

class C2GImport:
    def __init__(self):
        self.state = {}
        self.in_use = set()
        self.carids = {}
        self.dbfile = "car2go.db3"
        self.conn = sqlite3.connect(self.dbfile)
        self.conn.row_factory = sqlite3.Row
        self.c = self.conn.cursor()
        self.c.execute("PRAGMA foreign_keys=on;")
        self.run()

    def run(self):
        self.load_cars()
        self.load_data()
        self.c.execute("SELECT MAX(stamp) FROM car_state;");
        max_date_row = self.c.fetchone()
        if max_date_row[0] is not None:
            max_date = max_date_row[0]
            max_date_dt = datetime.datetime.fromtimestamp(max_date, tz=datetime.timezone(datetime.timedelta(hours=1)))
            print("Skipping already collected data until {}.".format(repr(max_date_dt)))
        else:
            max_date_dt = datetime.datetime.min.replace(tzinfo=datetime.timezone(datetime.timedelta(hours=1)))

        ctr = 0
        file_list = sorted(glob.glob(os.path.join("data/", "*.json")))
        file_count = len(file_list)
        for f in file_list:
            stamp = re.search(r'(\d{4}-\d\d-\d\d_\d{6})', f)
            stamp_str = stamp.group(1)
            stamp_dt  = datetime.datetime.strptime(stamp_str + "+0100", "%Y-%m-%d_%H%M%S%z")
            if stamp_dt <= max_date_dt:
                file_count -= 1
                continue
            ctr += 1
            self.scanfile(f, stamp_str, stamp_dt, ctr, file_count)
            if ctr%50==0:
                self.conn.commit()
        self.conn.commit()
        self.c.execute("VACUUM;")
        self.conn.close()

    def load_cars(self):
        print("Loading known cars from database.")
        self.c.execute("SELECT carId, plate FROM cars;")
        for row in self.c.fetchall():
            self.carids[row[1]] = row[0]

    def load_data(self):
        print("Load known states from database.")
        self.c.execute("SELECT c.plate, c.vin, cs.occupied, cs.address, cs.latitude, cs.longitude, cs.fuel, c.engineType, c.smartPhoneRequired, cs.interior_bad, cs.exterior_bad FROM car_state cs LEFT JOIN cars c ON cs.carId=c.carId;")
        for row in self.c:
            car_id = row[0]
            dataset = {
                "name": car_id,
                "vin": row[1],
                "occupied": True if row[2]==1 else False,
                "address": row[3],
                "coordinates": [row[5], row[4], 0],
                "fuel": row[6],
                "engineType": row[7],
                "smartPhoneRequired": True if row[8]==1 else False,
                "interior": "GOOD" if not row[9] else row[8],
                "exterior": "GOOD" if not row[10] else row[9],
            }
            self.state[car_id] = dataset
            if dataset["occupied"]:
                self.in_use.add(car_id)
            else:
                self.in_use.discard(car_id)

    def scanfile(self, filename, stamp_str, stamp_dt, file_count, files_total):
        print("File: {} ({}/{})".format(filename, file_count, files_total), end="")
        jf = open(filename, "r")
        doc = json.load(jf)
        jf.close()
        root = doc["placemarks"]
        print(" ({} cars)".format(len(root)), end="")
        self.parse_cars(stamp_dt, root)
        if file_count<files_total:
            print(ANSI_UP_DEL, end="")

    def parse_cars(self, stamp, placemarks):
        free_cars = set()
        changed_cars = set()

        # Walk all unoccupied cars
        for car_data in placemarks:
            car_id = car_data["name"]
            car_data["occupied"] = False
            if self.has_changed(car_data):
                changed_cars.add(car_id)
            free_cars.add(car_id)
            self.state[car_id] = car_data
            if car_id in self.in_use:
                self.in_use.remove(car_id)

        # Walk all known cars
        for car_id in self.state:
            if not car_id in free_cars and not car_id in self.in_use:
                # CAR GOT OCCUPIED
                self.state[car_id]["occupied"] = True
                self.in_use.add(car_id)
                changed_cars.add(car_id)

        for car_id in changed_cars:
            # Commit changes to database
            data = self.state[car_id]
            if not car_id in self.carids:
                self.c.execute(
                    "INSERT INTO cars (plate, vin, vinPrefix, smartPhoneRequired, engineType) VALUES (?,?,?,?,?)", (
                    car_id,
                    data["vin"],
                    data["vin"][0:9],
                    1 if data["smartPhoneRequired"] else 0,
                    data["engineType"]
                ))
                self.carids[car_id] = self.c.lastrowid

            self.c.execute(
                "INSERT INTO car_state (stamp, carId, occupied, address, latitude, longitude, fuel, charging, interior_bad, exterior_bad) VALUES (?,?,?,?,?,?,?,?,?,?)", (
                math.floor(stamp.timestamp()),
                self.carids[car_id],
                1 if data["occupied"] else 0,
                data["address"],
                data["coordinates"][1],
                data["coordinates"][0],
                data["fuel"],
                None if not "charging" in data else 1 if data["charging"] else 0,
                None if data["interior"] == "GOOD" else data["interior"],
                None if data["exterior"] == "GOOD" else data["exterior"]
            ))
            print(".", end="")
        print(" {}".format(len(changed_cars)))

    def has_changed(self, new_data):
        car_id = new_data["name"]
        if not car_id in self.state:
            return True
        old_data = self.state[car_id]

        for k in new_data:
            if old_data[k] != new_data[k]:
                #print("{} changed {}".format(car_id, k))
                return True

        return False

if __name__=="__main__":
    C2GImport()
