import requests


OSRM_URL = "http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}"


def get_route(start_lat, start_lon, end_lat, end_lon):
    """Call OSRM and return route distance (miles) and geometry."""
    url = OSRM_URL.format(
        lon1=start_lon, lat1=start_lat,
        lon2=end_lon, lat2=end_lat
    )
    params = {
        "overview": "full",
        "geometries": "geojson",
        "steps": "false",
    }
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    if data.get("code") != "Ok" or not data.get("routes"):
        raise ValueError("OSRM could not find a route")

    route = data["routes"][0]
    return {
        "distance_miles": route["distance"] / 1609.34,
        "geometry": route["geometry"],
        "coordinates": route["geometry"]["coordinates"],
    }