import csv
from decimal import Decimal, InvalidOperation
from django.core.management.base import BaseCommand
from routes.models import FuelStation


US_STATES = {
    'AL','AK','AZ','AR','CA','CO','CT','DE','FL','GA','HI','ID','IL','IN','IA','KS','KY','LA','ME',
    'MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ','NM','NY','NC','ND','OH','OK','OR','PA',
    'RI','SC','SD','TN','TX','UT','VT','VA','WA','WV','WI','WY'
}


class Command(BaseCommand):
    help = 'Import fuel prices from CSV'

    def add_arguments(self, parser):
        parser.add_argument('fuel_csv', type=str, help='Path to fuel prices CSV')
        parser.add_argument('cities_csv', type=str, help='Path to US cities CSV')

    def handle(self, *args, **options):
        fuel_csv = options['fuel_csv']
        cities_csv = options['cities_csv']

        city_coords = {}
        with open(cities_csv, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []
            state_col = 'state_id' if 'state_id' in fieldnames else 'state'
            for row in reader:
                try:
                    key = (row['city'].strip().lower(), row[state_col].strip().upper())
                    city_coords[key] = (float(row['lat']), float(row['lng']))
                except (KeyError, ValueError):
                    continue

        self.stdout.write(self.style.SUCCESS(f'Loaded {len(city_coords)} city coordinates'))

        stations = {}
        skipped = 0
        with open(fuel_csv, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                state = row['State'].strip().upper()
                if state not in US_STATES:
                    skipped += 1
                    continue

                city = row['City'].strip()
                key = (city.lower(), state)
                if key not in city_coords:
                    skipped += 1
                    continue

                lat, lon = city_coords[key]

                try:
                    price = Decimal(row['Retail Price'].strip())
                except (InvalidOperation, AttributeError):
                    skipped += 1
                    continue

                opis_id = row['OPIS Truckstop ID'].strip()

                if opis_id in stations:
                    if price < stations[opis_id]['retail_price']:
                        stations[opis_id]['retail_price'] = price
                else:
                    stations[opis_id] = {
                        'opis_id': opis_id,
                        'name': row['Truckstop Name'].strip(),
                        'address': row['Address'].strip(),
                        'city': city,
                        'state': state,
                        'rack_id': row['Rack ID'].strip(),
                        'retail_price': price,
                        'latitude': lat,
                        'longitude': lon,
                    }

        FuelStation.objects.all().delete()
        FuelStation.objects.bulk_create([FuelStation(**data) for data in stations.values()])

        self.stdout.write(self.style.SUCCESS(
            f'Imported {len(stations)} stations. Skipped {skipped} rows.'
        ))