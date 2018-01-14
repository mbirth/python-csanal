#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sqlite3

class C2GImport:
    def __init__(self):
        self.dbfile = "car2go.db3"
        self.conn = sqlite3.connect(self.dbfile)
        self.conn.row_factory = sqlite3.Row
        self.c = self.conn.cursor()
        self.c.execute("PRAGMA foreign_keys=on;")
        self.run()

    def run(self):
        self.c.execute("SELECT DISTINCT stamp FROM car_state ORDER BY stamp ASC;");
        stamps = []
        for row in self.c:
            stamps.append(row[0])

        print("Found {} time stamps.".format(len(stamps)))

        result = {}
        used_keys = []
        step_width = 1200   # 20 minutes between steps
        cur_step = -1
        cur_state = [[], []]
        for stamp in stamps:
            if stamp > cur_step + step_width:
                if cur_step > 0:
                    result[cur_step] = cur_state
                    cur_state = [[], []]    # first: removed cars, second: newly added cars
                cur_step = stamp
                used_keys.append(cur_step)
            self.c.execute("SELECT occupied, latitude, longitude FROM car_state WHERE stamp=?;", (stamp,));
            for row in self.c:
                point = [row[1], row[2], 0.8]
                if row[0]==0:
                    # Car got free
                    if point in cur_state[0]:
                        # car was marked as occupied, just remove marker
                        cur_state[0].remove(point)
                    else:
                        cur_state[1].append(point)
                else:
                    # Car got occupied
                    if point in cur_state[1]:
                        # car was marked as free, just remove marker
                        cur_state[1].remove(point)
                    else:
                        cur_state[0].append(point)

        result["keys"] = used_keys

        with open("maps/map_data.js", "wt") as f:
            f.write("window.data = ")
            f.write(json.dumps(result))
            f.write(";")


if __name__=="__main__":
    C2GImport()
