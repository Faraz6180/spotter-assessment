from geopy.geocoders import Nominatim

_geolocator = Nominatim(user_agent="spotter_assessment")


def geocode(location: str):
    """Return (lat, lon) for a location string like 'Chicago, IL'."""
    loc = _geolocator.geocode(location, timeout=15)
    if not loc:
        raise ValueError(f"Could not geocode: {location}")
    return loc.latitude, loc.longitude