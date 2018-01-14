#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import geopy.distance
import json
import math
import os
import glob
import re
import sys

class C2GAnalyse:
    def __init__(self):
        self.state = {}
        self.in_use = []
        self.total_minutes = 0.0
        self.total_money = 0.0
        self.total_distance = 0.0
        self.run()

    def find_car_type(self, vin):
        # 1..3 = manufacturer code
        # 4..6 = general type
        # 7    = body form
        # 8..9 = engine type
        # 10   = steering (1=left, 2=right)
        # 11   = manufacturing facilty
        seg = vin[0:9]
        typelist = {
            "WDD117342": ["CLA 180", 0.34],
            "WDC156912": ["GLA 180 CDI", 0.34],
            "WDC156942": ["GLA 180", 0.34],
            "WDC156943": ["GLA 200", 0.34],
            "WDD176012": ["A 180 CDI", 0.31],
            "WDD176042": ["A 180", 0.31],
            "WDD176043": ["A 200", 0.31],
            "WDD246242": ["B 180", 0.34],
            "WME451334": ["smart fortwo 451", 0.26],
            "WME451390": ["smart fortwo 451 ed", 0.29],
            "WME451391": ["smart fortwo 451 ed", 0.29],
            "WME453342": ["smart fortwo 453", 0.26],
        }

        if not seg in typelist:
            print("Missing vehicle type for {} (VIN {})!".format(seg, vin))

        return typelist[seg]

    def run(self):
        for f in sorted(glob.glob(os.path.join("../data/", "*.json"))):
            self.scanfile(f)
        print("{} cars seen in total.".format(len(self.state)))
        print("Total kilometres driven: {}".format(self.total_distance))
        print("Total minutes driven: {}".format(self.total_minutes))
        print("Total money made: {}".format(self.total_money))

    def scanfile(self, filename):
        stamp = re.search(r'(\d{4}-\d\d-\d\d_\d{6})', filename)
        stamp_str = stamp.group(1)
        stamp_dt  = datetime.datetime.strptime(stamp_str, "%Y-%m-%d_%H%M%S")
        print("File: {} ({}, Totals: {:.3f}km, {:.1f}mins, {:.2f}€)".format(filename, stamp_str, self.total_distance, self.total_minutes, self.total_money), end="")
        jf = open(filename, "r")
        doc = json.load(jf)
        jf.close()
        root = doc["placemarks"]
        print(" ({} cars available)".format(len(root)))
        self.parse_cars(stamp_dt, root)

    def parse_cars(self, stamp, placemarks):
        not_in_use = []
        for pm in placemarks:
            self.update_car(stamp, pm)
            not_in_use.append(pm["name"])
        for car_id in self.state:
            if not car_id in not_in_use:
                if not car_id in self.in_use:
                    print("{} OCCUPIED!".format(car_id))
                    self.state[car_id]["occupied"] = stamp
                    self.in_use.append(car_id)
            else:
                if car_id in self.in_use:
                    #print("{} RETURNED!".format(car_id))
                    if "occupied" in self.state[car_id]:
                        del self.state[car_id]["occupied"]
                    self.in_use.remove(car_id)

    def update_car(self, stamp, new_data):
        car_id = new_data["name"]
        if car_id in self.state:
          old_data = self.state[car_id]
          car_type = self.find_car_type(new_data["vin"])
          if new_data["address"] != old_data["address"]:
              ## CAR MOVED
              old_spot = (old_data["coordinates"][1], old_data["coordinates"][0])
              new_spot = (new_data["coordinates"][1], new_data["coordinates"][0])
              distance = geopy.distance.distance(old_spot, new_spot).kilometers
              if not "occupied" in old_data:
                  old_data["occupied"] = "unknown"
                  minutes = -1
              else:
                  minutes = (stamp - old_data["occupied"]).total_seconds() / 60
                  self.total_minutes += minutes
                  self.total_money += math.ceil(minutes) * car_type[1]
                  self.total_distance += distance

              print("{} {} moved for {:.3f}km/{:.1f}mins: {} ({}%, {}, {}) {} -> {} {} ({}%, {}, {})".format(
                  car_type[0],
                  car_id,
                  distance,
                  minutes,
                  old_data["address"],
                  old_data["fuel"],
                  old_data["interior"],
                  old_data["exterior"],
                  old_data["occupied"],
                  stamp,
                  new_data["address"],
                  new_data["fuel"],
                  new_data["interior"],
                  new_data["exterior"]
              ))
          elif new_data["fuel"] != old_data["fuel"]:
              print("{} FUEL CHANGE: {} -> {}".format(car_id, old_data["fuel"], new_data["fuel"]))
          if new_data["vin"] != old_data["vin"]:
              print("{} ################# VIN CHANGE!!!".format(car_id))
        self.state[car_id] = new_data

if __name__=="__main__":
    C2GAnalyse()
