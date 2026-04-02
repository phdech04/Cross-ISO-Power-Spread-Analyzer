CREATE TABLE IF NOT EXISTS hourly_prices (
    timestamp TIMESTAMP,
    iso VARCHAR(10),
    node VARCHAR(50),
    lmp DECIMAL(10,2),
    energy_component DECIMAL(10,2),
    congestion_component DECIMAL(10,2),
    loss_component DECIMAL(10,2),
    PRIMARY KEY (timestamp, iso, node)
);

CREATE TABLE IF NOT EXISTS hourly_weather (
    timestamp TIMESTAMP,
    iso VARCHAR(10),
    temp_c DECIMAL(5,1),
    wind_speed DECIMAL(5,1),
    solar_radiation DECIMAL(8,2),
    humidity DECIMAL(5,1),
    cdd DECIMAL(5,1),
    hdd DECIMAL(5,1),
    PRIMARY KEY (timestamp, iso)
);
