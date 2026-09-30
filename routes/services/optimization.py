"""
Greedy fuel stop optimizer.

Assumptions:
- Tank capacity = 50 gallons (500 miles at 10 MPG)
- Vehicle starts with a FULL tank
- Fuel is only bought at stations in the list
"""

TANK_GALLONS = 50.0
MPG = 10.0
MAX_RANGE_MILES = TANK_GALLONS * MPG  # 500 miles


def optimize_fuel(stations, total_distance_miles):
    """
    stations: list of dicts with 'distance' (miles from start), 'price', 'name', 'lat', 'lon'
              sorted by 'distance'
    total_distance_miles: total trip distance
    Returns: (list_of_fuel_stops, total_cost)
    """
    points = [{
        "distance": 0.0, "price": None, "name": "START", "lat": None, "lon": None,
    }]
    for s in stations:
        if 0 < s["distance"] < total_distance_miles:
            points.append({
                "distance": s["distance"], "price": s["price"],
                "name": s["name"], "lat": s["lat"], "lon": s["lon"],
            })
    points.append({
        "distance": total_distance_miles, "price": None,
        "name": "DESTINATION", "lat": None, "lon": None,
    })

    fuel_stops = []
    total_cost = 0.0
    current_index = 0
    fuel = TANK_GALLONS

    max_iterations = len(points) * 2
    iterations = 0

    while current_index < len(points) - 1 and iterations < max_iterations:
        iterations += 1
        current = points[current_index]
        fuel_range = fuel * MPG
        reachable_until = current["distance"] + fuel_range

        reachable = [
            (i, p) for i, p in enumerate(points)
            if i > current_index and p["distance"] <= reachable_until
        ]

        if not reachable:
            raise ValueError(
                f"Trip not possible: no station within range from "
                f"{current['name']} at mile {current['distance']:.1f}"
            )

        dest_index = len(points) - 1
        if any(i == dest_index for i, _ in reachable):
            fuel -= (points[dest_index]["distance"] - current["distance"]) / MPG
            break

        # Pick cheapest reachable station (with a price)
        candidates = [(i, p) for i, p in reachable if p["price"] is not None]
        if not candidates:
            raise ValueError("No priced stations in range")

        cheapest_index, cheapest = min(candidates, key=lambda x: x[1]["price"])
        current_price = current["price"]

        # If current is cheapest in range (or it's START), fill up
        if current_price is None or all(
            p["price"] is None or p["price"] >= current_price for _, p in candidates
        ):
            if current_price is not None:
                gallons_to_buy = TANK_GALLONS - fuel
                if gallons_to_buy > 0:
                    total_cost += gallons_to_buy * float(current_price)
                    fuel_stops.append({
                        "name": current["name"],
                        "lat": current["lat"],
                        "lon": current["lon"],
                        "distance_miles": round(current["distance"], 2),
                        "price_per_gallon": float(current_price),
                        "gallons": round(gallons_to_buy, 2),
                        "cost": round(gallons_to_buy * float(current_price), 2),
                    })
                    fuel = TANK_GALLONS
            drive_distance = cheapest["distance"] - current["distance"]
            fuel -= drive_distance / MPG
            current_index = cheapest_index
        else:
            # Cheaper station ahead — buy just enough
            drive_distance = cheapest["distance"] - current["distance"]
            needed_fuel = drive_distance / MPG
            if needed_fuel > fuel:
                gallons_to_buy = needed_fuel - fuel
                total_cost += gallons_to_buy * float(current_price)
                fuel_stops.append({
                    "name": current["name"],
                    "lat": current["lat"],
                    "lon": current["lon"],
                    "distance_miles": round(current["distance"], 2),
                    "price_per_gallon": float(current_price),
                    "gallons": round(gallons_to_buy, 2),
                    "cost": round(gallons_to_buy * float(current_price), 2),
                })
                fuel = needed_fuel
            fuel -= drive_distance / MPG
            current_index = cheapest_index

    return fuel_stops, round(total_cost, 2)