Spotter Assessment — Django Fuel Route API
A Django REST API that calculates the optimal fuel stops along a driving route in the USA.

Given a start and finish location, the API returns:

The route on a map (GeoJSON)

The optimal fuel stops along the route

The total cost of fuel for the trip

Requirements
Python 3.10+

Django 4.x / 5.x

A free US cities dataset (see setup)

Setup
1. Clone the repository
bash
git clone https://github.com/Faraz6180/spotter-assessment.git
cd spotter-assessment
2. Create and activate a virtual environment
bash
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate        # Mac / Linux
3. Install dependencies
bash
pip install -r requirements.txt
4. Download the US cities dataset
The fuel prices CSV does not include latitude/longitude. To place stations on a map, we geocode each city using a free offline dataset.

Download the Basic (free) version of the US Cities Database from:
https://simplemaps.com/data/us-cities

Extract the zip.

Copy the file uscities.csv into the project root and rename it to:

text
us_cities.csv
5. Add the fuel prices CSV
Place the provided file fuel-prices-for-be-assessment.csv in the project root (same folder as manage.py).

6. Run database migrations
bash
python manage.py migrate
7. Import the fuel stations
bash
python manage.py import_fuel fuel-prices-for-be-assessment.csv us_cities.csv
Expected output:

text
Loaded 31186 city coordinates
Imported 6092 stations. Skipped 1217 rows.
8. Start the server
bash
python manage.py runserver
The API will be available at http://127.0.0.1:8000/.

API Usage
Endpoint
text
POST /api/route/
Request body
json
{
  "start": "Los Angeles, CA",
  "finish": "New York, NY"
}
Example — PowerShell
powershell
$body = '{"start":"Los Angeles, CA","finish":"New York, NY"}'
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/route/" `
  -Method Post -Body $body -ContentType "application/json"
Example — cURL
bash
curl -X POST http://127.0.0.1:8000/api/route/ \
  -H "Content-Type: application/json" \
  -d '{"start": "Los Angeles, CA", "finish": "New York, NY"}'
Response
json
{
  "start": { "lat": 34.053, "lon": -118.242, "name": "Los Angeles, CA" },
  "finish": { "lat": 40.712, "lon": -74.006, "name": "New York, NY" },
  "total_distance_miles": 2793.56,
  "total_cost_usd": 737.66,
  "fuel_stops": [
    {
      "name": "Maverik #674",
      "lat": 36.2883,
      "lon": -115.0888,
      "distance_miles": 250.79,
      "price_per_gallon": 3.28233,
      "gallons": 25.08,
      "cost": 82.32
    }
  ],
  "route_geojson": {
    "type": "LineString",
    "coordinates": [[-118.24, 34.05], ...]
  }
}
You can paste the route_geojson value into https://geojson.io to view the route on a map.

How It Works
1. Geocoding
The start and finish strings are geocoded using Nominatim (OpenStreetMap) through the geopy library. This is done once per request.

2. Routing
The API calls OSRM (Open Source Routing Machine) exactly once per request to obtain the route geometry (GeoJSON LineString) and total distance in miles. No API key is required.

3. Station filtering
All fuel stations from the database are filtered to those within 5 miles of the route. This is done using Shapely — the route is treated as a LineString, and each station's distance to that line is computed. Stations far from the route are discarded.

4. Fuel optimization
A greedy algorithm picks the optimal set of fuel stops.

Assumptions:

Tank capacity: 50 gallons

Fuel efficiency: 10 miles per gallon

Maximum range: 500 miles on a full tank

Vehicle starts with a full tank

Fuel is only purchased at stations along the route

Algorithm logic:

At each station, look at all stations within range.

If there is a cheaper station ahead in range, buy just enough fuel to reach it.

Otherwise, fill up and drive to the cheapest station in range.

Repeat until the destination is reached.

This produces a cost-optimal solution in a single pass.

Project Structure
text
spotter-assessment/
├── manage.py
├── fuel-prices-for-be-assessment.csv     # Provided fuel price data
├── us_cities.csv                          # US cities lat/lon (download separately)
├── requirements.txt
├── README.md
├── spotter_project/                       # Django project settings
│   ├── settings.py
│   └── urls.py
└── routes/                                # Main app
    ├── models.py                          # FuelStation model
    ├── views.py                           # API view
    ├── urls.py                            # Route URL
    ├── services/
    │   ├── geocoding.py                   # Nominatim geocoder
    │   ├── routing.py                     # OSRM routing client
    │   └── optimization.py                # Greedy fuel optimizer
    └── management/
        └── commands/
            └── import_fuel.py             # CSV importer
Data Notes
The provided fuel prices CSV contains:

Column	Description
OPIS Truckstop ID	Unique truckstop identifier
Truckstop Name	Name of the fuel station
Address	Street address or highway exit
City, State	Location
Rack ID	Fuel rack identifier
Retail Price	Price per gallon (USD)
Stations are grouped by OPIS ID, keeping the minimum retail price when duplicates exist. Canadian stations are ignored because the API is restricted to the USA.

Tech Stack
Django + Django REST Framework — API

OSRM — free routing engine (no API key)

Nominatim (via geopy) — geocoding

Shapely — geometric distance filtering

SQLite — default database (easy local setup)

Limitations & Future Work
Stations are filtered using a simple 5-mile corridor around the route. In dense areas, this could include stations that are technically off-highway.

Only one routing provider (OSRM) is used. In production, a paid service like Google Maps would give more accurate ETAs.

Geocoding via Nominatim is rate-limited. For production, a paid geocoder (e.g., Mapbox, Google) would be more reliable.

The optimizer assumes price does not change over time.

Author
Faraz Mubeen
Submitted for the Spotter Backend Django Engineer assessment.
