from flask import Flask, request, jsonify, render_template
from azure.cosmos import CosmosClient, PartitionKey
import math
import os
import random

app = Flask(__name__)

# Endpoint for the home page
@app.route('/')
def home():
    return render_template('index.html')

# Cosmos DB configuration from environment variables
endpoint = "https://zabka.documents.azure.com:443/"
key = "S74XazFN5QsBrJKp2FFh1g3X6h3AZefLkEwHQG0IWIZvDRXtC0C1EAIGZsR0vlGq2nPVmB4FILEcACDbdE58Lg=="
database_name = 'zabkaDatabase'
stores_container_name = 'zabkaContainer'
clients_container_name = 'klientContainer'

client = CosmosClient(endpoint, key)
database = client.get_database_client(database_name)
stores_container = database.get_container_client(stores_container_name)
clients_container = database.get_container_client(clients_container_name)


def calculate_distance(lat1, lon1, lat2, lon2):
    # Haversine formula to calculate distance between two points on the Earth
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(math.radians(lat1)) * math.cos(
        math.radians(lat2)) * math.sin(dlon / 2) * math.sin(dlon / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance


@app.route('/find-nearest-store', methods=['GET'])
def find_nearest_store():
    app.logger.info("Request to /find-nearest-store received")

    # Pobieranie wszystkich klientów
    clients = list(clients_container.read_all_items())
    if not clients:
        app.logger.warning("No clients found")
        return jsonify({"error": "No clients found"}), 404

    # Wybieranie losowego klienta
    client = random.choice(clients)
    app.logger.info(f"Selected client: {client}")

    client_lat = float(client['x'].replace(',', '.'))
    client_lon = float(client['y'].replace(',', '.'))
    wymagania = client['wymagania']

    # Pobieranie wszystkich żabek
    zabki_df = list(stores_container.read_all_items())

    # Filtrowanie żabek zgodnie z wymaganiami klienta
    if wymagania == 'p':
        mozliwe_zabki = [zabka for zabka in zabki_df if zabka['punkt_pocztowy'] == 'tak']
    elif wymagania == 'w':
        mozliwe_zabki = [zabka for zabka in zabki_df if zabka['wozek'] == 'tak']
    elif wymagania == 'oba':
        mozliwe_zabki = [zabka for zabka in zabki_df if zabka['punkt_pocztowy'] == 'tak' and zabka['wozek'] == 'tak']
    else:
        mozliwe_zabki = zabki_df

    app.logger.info(f"Filtered stores: {mozliwe_zabki}")

    # Znalezienie najbliższej żabki
    nearest_store = None
    min_distance = float('inf')

    for store in mozliwe_zabki:
        store_lat = float(store['x'].replace(',', '.'))
        store_lon = float(store['y'].replace(',', '.'))
        distance = calculate_distance(client_lat, client_lon, store_lat, store_lon)
        if distance < min_distance:
            min_distance = distance
            nearest_store = store

    if nearest_store:
        app.logger.info(f"Nearest store: {nearest_store}")
        return f"""
            <html>
            <head>
                <title>Nearest Store Details</title>
            </head>
            <body>
                <h2>Nearest Store Details:</h2>
                <p><strong>Name:</strong> {nearest_store['nazwa']}</p>
                <p><strong>id:</strong> {nearest_store['id']}</p>
                <p><strong>Distance:</strong> {min_distance:.2f} km</p>
            </body>
            </html>
        """
    else:
        app.logger.warning("No matching stores found")
        return jsonify({"error": "No matching stores found"}), 404


if __name__ == '__main__':
    app.run(debug=True)
