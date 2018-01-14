PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=on;

-- VIN digits:
-- 1..3 = manufacturer code
-- 4..6 = general type
-- 7    = body form
-- 8..9 = engine type
-- 10   = steering (1=left, 2=right)
-- 11   = manufacturing facilty
CREATE TABLE "car_models" (
  "vinPrefix" TEXT PRIMARY KEY,
  "model" TEXT NOT NULL,
  "subtype" TEXT,
  "pricePerMinute" REAL
);

INSERT INTO "car_models" ("vinPrefix", "model", "subtype", "pricePerMinute") VALUES
  ("WDD117342", "CLA", "180", 0.34),
  ("WDC156912", "GLA", "180 CDI", 0.34),
  ("WDC156942", "GLA", "180", 0.34),
  ("WDC156943", "GLA", "200", 0.34),
  ("WDD176012", "A", "180 CDI", 0.31),
  ("WDD176042", "A", "180", 0.31),
  ("WDD176043", "A", "200", 0.31),
  ("WDD242890", "B", "ed", 0.34),
  ("WDD246242", "B", "180", 0.34),
  ("WME451334", "smart", "fortwo 451 coupé mhd", 0.26),
  ("WME451390", "smart", "fortwo 451 coupé ed", 0.29),
  ("WME451391", "smart", "fortwo 451 coupé ed", 0.29),
  ("WME451392", "smart", "fortwo 451 coupé ed (Brabus)", 0.29),
  ("WME453391", "smart", "fortwo 453 coupé ed", 0.29),
  ("WME453342", "smart", "fortwo 453 coupé", 0.26)
;

CREATE TABLE "cars" (
  "carId" INTEGER PRIMARY KEY AUTOINCREMENT,
  "plate" TEXT NOT NULL,
  "vin" TEXT,
  "vinPrefix" TEXT REFERENCES "car_models" ("vinPrefix"),
  "smartPhoneRequired" INTEGER,
  "engineType" TEXT
);

-- Plates can't have different VINs and vice versa
CREATE UNIQUE INDEX "idx_cars" ON "cars" ("plate", "vin");

CREATE VIEW "cars_detailed" AS
  SELECT c.carId, c.plate, cm.model, cm.subtype, cm.pricePerMinute, c.vin, c.smartPhoneRequired, c.engineType
  FROM "cars" c
  LEFT JOIN "car_models" cm ON c.vinPrefix=cm.vinPrefix;

-- TEST
CREATE VIEW "cars_detailed2" AS
  SELECT c.carId, c.plate, cm.model, cm.subtype, cm.pricePerMinute, c.vin, c.smartPhoneRequired, c.engineType
  FROM "cars" c
  LEFT JOIN "car_models" cm ON substr(c.vin, 1, 9)=cm.vinPrefix;

CREATE TABLE "car_state" (
  "stamp" INTEGER NOT NULL,
  "carId" INTEGER NOT NULL REFERENCES "cars" ("carId"),
  "occupied" INTEGER,
  "address" TEXT,
  "latitude" REAL,
  "longitude" REAL,
  "fuel" INTEGER,
  "charging" INTEGER,
  "interior_bad" TEXT,
  "exterior_bad" TEXT
);

-- A car can only have one state at a time
CREATE UNIQUE INDEX "idx_car_state" ON "car_state" ("stamp", "carId");

CREATE VIEW "car_state_human" AS
  SELECT datetime(stamp, "unixepoch", "localtime") AS "datetime", * FROM "car_state" ORDER BY stamp ASC;

CREATE VIEW "car_statechanges_count" AS
  SELECT cs.carId, ca.plate, cm.model, cm.subtype, COUNT(*) AS stateChanges
  FROM "car_state" cs
  LEFT JOIN "cars" ca ON cs.carId=ca.carId
  LEFT JOIN "car_models" cm ON ca.vinPrefix=cm.vinPrefix
  GROUP BY cs.carId
  ORDER BY stateChanges DESC;

-- To be filtered by carId or plate
CREATE VIEW "car_history" AS
  SELECT cs."datetime", cs.carId, c.plate, cs.occupied, cs.address, cs.latitude, cs.longitude, cs.fuel, cs.charging, c.vin, c.engineType, cs.interior_bad, cs.exterior_bad, c.smartPhoneRequired
  FROM "car_state_human" cs
  LEFT JOIN "cars" c ON cs.carId=c.carId
  ORDER BY stamp ASC;

CREATE TABLE "trips" (
  carId INTEGER REFERENCES "cars" ("carId"),
  stamp_departure INTEGER,
  stamp_arrival INTEGER,
  duration_minutes REAL,
  distance_km REAL,
  fuel_spent INTEGER,
  price REAL,
  FOREIGN KEY ("carId", "stamp_departure") REFERENCES "car_state" ("carId", "stamp"),
  FOREIGN KEY ("carId", "stamp_arrival") REFERENCES "car_state" ("carId", "stamp")
);

CREATE VIEW "trips_details" AS
  SELECT
    cd.plate, cd.model, cd.subtype, cs1.address AS "address_departure", cs2.address AS "address_arrival",
    datetime(t.stamp_departure, "unixepoch", "localtime") AS "time_departure",
    datetime(t.stamp_arrival, "unixepoch", "localtime") AS "time_arrival",
    t.duration_minutes, t.distance_km, t.fuel_spent, t.price,
    t.stamp_departure, cs1.latitude AS "latitude_departure", cs1.longitude AS "longitude_departure",
    t.stamp_arrival, cs2.latitude AS "latitude_arrival", cs2.longitude AS "longitude_arrival",
    cs1.fuel AS "fuel_departure", cs2.fuel AS "fuel_arrival",
    cd.vin, cd.pricePerMinute, cd.engineType
  FROM trips t
  LEFT JOIN car_state cs1 ON t.carId=cs1.carId AND t.stamp_departure=cs1.stamp
  LEFT JOIN car_state cs2 ON t.carId=cs2.carId AND t.stamp_arrival=cs2.stamp
  LEFT JOIN cars_detailed cd ON t.carId=cd.carId
  ORDER BY t.stamp_departure ASC;
