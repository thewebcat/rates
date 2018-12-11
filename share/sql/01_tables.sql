CREATE TABLE IF NOT EXISTS pairs (
  id   SERIAL PRIMARY KEY,
  symbol CHAR(6) NOT NULL
);

INSERT INTO "public"."pairs" ("id", "symbol")
VALUES (DEFAULT, 'EURUSD'),
       (DEFAULT, 'USDJPY'),
       (DEFAULT, 'GBPUSD'),
       (DEFAULT, 'AUDUSD'),
       (DEFAULT, 'USDCAD');

CREATE TABLE IF NOT EXISTS points (
  id   SERIAL PRIMARY KEY,
  pair_id INT NOT NULL REFERENCES pairs(id),
  timestamp TIMESTAMPTZ DEFAULT Now(),
  value REAL DEFAULT 0 NOT NULL
);

CREATE INDEX timestamp_idx ON points USING hash ("timestamp");