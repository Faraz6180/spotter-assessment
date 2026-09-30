from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from shapely.geometry import LineString, Point

from .models import FuelStation
from .services.routing import get_route
from .services.geocoding import geocode
from .services.optimization import optimize_fuel


MILES_PER_DEGREE = 69.0


class RouteFuelView(APIView):
    def post(self, request):
        start = request.data.get("start")
        finish = request.data.get("finish")

        if not start or not finish:
            return Response(
                {"error": "Provide 'start' and 'finish' in the request body."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            start_lat, start_lon = geocode(start)
            end_lat, end_lon = geocode(finish)

            route = get_route(start_lat, start_lon, end_lat, end_lon)
            total_distance = route["distance_miles"]
            coords = route["coordinates"]

            line = LineString([(lon, lat) for lon, lat in coords])

            stations_near = []
            for s in FuelStation.objects.all():
                if s.latitude is None or s.longitude is None:
                    continue
                point = Point(s.longitude, s.latitude)
                dist_miles = line.distance(point) * MILES_PER_DEGREE
                if dist_miles > 5:
                    continue
                along_deg = line.project(point)
                along_miles = (along_deg / line.length) * total_distance
                stations_near.append({
                    "name": s.name,
                    "lat": s.latitude,
                    "lon": s.longitude,
                    "price": float(s.retail_price),
                    "distance": along_miles,
                })

            stations_near.sort(key=lambda x: x["distance"])

            fuel_stops, total_cost = optimize_fuel(stations_near, total_distance)

            return Response({
                "start": {"lat": start_lat, "lon": start_lon, "name": start},
                "finish": {"lat": end_lat, "lon": end_lon, "name": finish},
                "total_distance_miles": round(total_distance, 2),
                "total_cost_usd": total_cost,
                "fuel_stops": fuel_stops,
                "route_geojson": route["geometry"],
            })

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": f"Unexpected error: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )