import pandas as pd
import numpy as np

# Let's seed a bunch of major CA zip codes with rough lat/lons
zctas = [
    # Los Angeles
    (90001, "Los Angeles", 33.97, -118.24), (90011, "Los Angeles", 34.00, -118.25), (90012, "Los Angeles", 34.06, -118.23),
    (90210, "Los Angeles", 34.09, -118.40), (90291, "Los Angeles", 33.99, -118.45), (90022, "Los Angeles", 34.02, -118.15),
    (91331, "Los Angeles", 34.25, -118.42), (90044, "Los Angeles", 33.95, -118.28), (90650, "Los Angeles", 33.90, -118.08),
    (91402, "Los Angeles", 34.22, -118.44),
    # Inland Empire
    (92404, "Inland Empire", 34.13, -117.27), (92335, "Inland Empire", 34.09, -117.43), (92503, "Inland Empire", 33.93, -117.42),
    (92883, "Inland Empire", 33.78, -117.50), (92201, "Inland Empire", 33.71, -116.22), (92231, "Inland Empire", 32.67, -115.49),
    # San Diego
    (92101, "San Diego", 32.71, -117.16), (92113, "San Diego", 32.69, -117.11), (92114, "San Diego", 32.70, -117.08),
    (92154, "San Diego", 32.70, -117.05), (91910, "San Diego", 32.63, -117.06), (92058, "San Diego", 33.22, -117.34),
    # SF / Bay Area
    (94102, "Bay Area", 37.78, -122.41), (94103, "Bay Area", 37.77, -122.41), (94110, "Bay Area", 37.74, -122.41),
    (94124, "Bay Area", 37.73, -122.38), (94601, "Bay Area", 37.77, -122.21), (94621, "Bay Area", 37.75, -122.19),
    (94801, "Bay Area", 37.94, -122.37), (95116, "Bay Area", 37.35, -121.84), (95122, "Bay Area", 37.33, -121.82),
    (94565, "Bay Area", 38.01, -121.87),
    # Central Valley
    (93706, "Central Valley", 36.73, -119.82), (93725, "Central Valley", 36.72, -119.74), (93702, "Central Valley", 36.73, -119.78),
    (93307, "Central Valley", 35.33, -118.96), (93257, "Central Valley", 35.63, -119.24), (93612, "Central Valley", 36.81, -119.69),
    (93291, "Central Valley", 36.33, -119.30), (95205, "Central Valley", 37.95, -121.25), (95350, "Central Valley", 37.96, -121.28),
    # Sacramento
    (95823, "Sacramento", 38.48, -121.43), (95824, "Sacramento", 38.51, -121.45), (95815, "Sacramento", 38.51, -121.46),
    (95838, "Sacramento", 38.63, -121.45), (95240, "Sacramento", 38.12, -121.25),
]

data = []
np.random.seed(42)
for zcta, region, lat, lon in zctas:
    base_pb = 80 if region in ["Central Valley", "Inland Empire", "Los Angeles"] else 60
    pb = np.clip(np.random.normal(base_pb, 10), 0, 100)
    
    td = np.random.normal(8500, 1500) if region == "Los Angeles" else np.random.normal(6000, 1500)
    td = np.clip(td, 2000, 15000)
    
    gap = np.random.normal(7, 2) if region in ["Inland Empire", "Central Valley"] else np.random.normal(4, 1.5)
    gap = np.clip(gap, 0, 15)
    
    pm = (pb * 0.15) + np.random.normal(1, 0.5)
    d_pm = (td * 0.0002) + np.random.normal(0.5, 0.2)
    share = np.clip((pb / 100) * 0.9 + np.random.normal(0, 0.1), 0, 1)
    
    ghg = gap * 0.8 + np.random.normal(0, 0.5)
    
    data.append({
        "zcta": str(zcta),
        "region": region,
        "lat": lat,
        "lon": lon,
        "pollution_burden": round(pb, 1),
        "traffic_density": int(td),
        "pm25": round(pm, 2),
        "diesel_pm": round(d_pm, 2),
        "disadvantaged_share": round(share, 3),
        "vmt_gap_index": round(gap, 1),
        "ghg_per_capita": round(ghg, 2)
    })

df = pd.DataFrame(data)
df.to_csv("data/app/ca_zcta_spatial.csv", index=False)
print("done")
