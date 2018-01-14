Car Sharing Analyser
====================

This is a collection of scripts and tools to gather, prepare and analyse data about a
German car sharing company.


Gathering
---------

The script `getData.sh` collects a JSON dump from the webpage every 30 seconds and stores
that into the `data/` folder. A week's worth of data is about 3.3 GiB.

Edit the file first to configure your desired city. Then let it run in a tmux session.


Preparing
---------

`init_db.sh` will create a SQLite database file according to `sql/dbschema.sql`.

Make sure you have Python 3 installed. Install required Python packages by running:

    sudo -H pip3 install -r requirements.txt

(Or use virtualenv, pipenv, venv, etc.)

Then run `import.py` to import all the JSON dumps into the database. If you continue the data
collection, you can run `import.py` later to import the new data. Successfully imported JSON
dumps can be deleted, of course.

Importing a week's worth of data takes about 5 minutes and results in a 14.5 MiB
SQLite3 database.


Analysing
---------

Run `calc_trips.py` to analyse car's state changes and calculate possible(!) trips from it.
The trips data is written back into the database. (Trips shorter than 70 seconds are filtered.
See notes below.) A week's worth of trip data increases the database by about 4 MiB.

You can also use this script as a starting point for your own analysing scripts.
(Pull requests are welcome.)

For working with the database itself, I recommend
[DB Browser for SQLite](http://sqlitebrowser.org/).


### Example Queries

To see the history of a specific car, you can run e.g. (`XYZ` = number plate):

    SELECT * FROM car_history WHERE plate="XYZ";

To see cars in a specific area, you can run:

    SELECT *
    FROM car_history
    WHERE latitude>=52.515652 AND longitude>=13.372373
    AND   latitude<=52.516813 AND longitude<=13.378115;

Also check out the views in the database.


Notes
=====

* The `distance_km` is beeline from starting point to end point. If somebody runs errands and parks
  in the exact same spot, the distance is (almost) 0.
* You can't distinguish between these cases with distances of (almost) zero and no petrol spent:
  * a car that made a short trip and parked in the same spot,
  * a car that has been taken out of service for a while,
  * a car that has been reserved (possible for up to 30 minutes) but the reservation expired
* "Trips" over several days are most probably cars that have been taken out of service.
* A car that has been "reserved" (for up to 30 minutes) disappears from the list of cars. The
  reservation time is included in the trip's `duration_minutes`.
* The calculated prices don't factor in additional fees (airport, drop-off), the time a car was
  "reserved", and are also calculated for cars taken offline, i.e. where no money was paid by
  the customer.
* Smaller negative `fuel_spent` values are probably because the car was parked on a slope.
* The id for a car is it's number plate. Theoretically, a `plate` could be put on another
  vehicle (with a different `vin`). But this is very unlikely.
