from flask import Flask, request, jsonify, render_template
from azure.cosmos import CosmosClient
import math
import random
import matplotlib.pyplot as plt
import io
import base64
from azure.storage.blob import BlobServiceClient

app = Flask(__name__)

# Konfiguracja Azure Blob Storage
connect_str = "DefaultEndpointsProtocol=https;AccountName=zabkastorage;AccountKey=2WpfZHZetOlA000Z+hMnJn4RfRSSWS2V074ibx3iD9z5/5fww7qii/i/TIU6VBspoAO29lqlLYoJ+AStw5jMgw==;EndpointSuffix=core.windows.net"
container_name = "zabkastorage"
blob_service_client = BlobServiceClient.from_connection_string(connect_str)
container_client = blob_service_client.get_container_client(container_name)

# endpointy dla strony glownej
@app.route('/')
def home():
    return render_template('index.html')

# Konfiguracja Cosmos DB zmiennymi środowiskowymi
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
    # Formula Haversine do obliczania odległości między dwoma punktami na Ziemi
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) * math.sin(dlon / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance

@app.route('/find-nearest-store', methods=['GET'])
def find_nearest_store():
    app.logger.info("Request to /find-nearest-store received")

    #pobieranie wszystkich klientow
    clients = list(clients_container.read_all_items())
    if not clients:
        app.logger.warning("No clients found")
        return jsonify({"error": "No clients found"}), 404

    # wybieranie losowego klienta
    client = random.choice(clients)
    app.logger.info(f"Selected client: {client}")

    # wyciąganie wspolrzednych klienta
    client_lat = float(client['y'].replace(',', '.'))  # latitude
    client_lon = float(client['x'].replace(',', '.'))  # longitude
    wymagania = client['wymagania']

    #pobieranie wzsystkich sklepow
    zabki_df = list(stores_container.read_all_items())

    #filtrowanie sklepow wedlug wymagan klienta
    if wymagania == 'p':
        mozliwe_zabki = [zabka for zabka in zabki_df if zabka['punkt_pocztowy'] == 'tak']
    elif wymagania == 'w':
        mozliwe_zabki = [zabka for zabka in zabki_df if zabka['wozek'] == 'tak']
    elif wymagania == 'oba':
        mozliwe_zabki = [zabka for zabka in zabki_df if zabka['punkt_pocztowy'] == 'tak' and zabka['wozek'] == 'tak']
    else:
        mozliwe_zabki = zabki_df

    app.logger.info(f"Filtered stores: {mozliwe_zabki}")

    # generowanie wykresu ze wszystkimi sklepami i klientem
    plt.figure(figsize=(10, 8))

    #dodawanie pozycji klienta
    plt.plot(client_lon, client_lat, 'rx', markersize=10, label='Selected Client')  # 'rx' means red cross

    nearest_store = None
    min_distance = float('inf')

    for zabka in zabki_df:
        x = float(zabka['y'].replace(',', '.'))  # latitude
        y = float(zabka['x'].replace(',', '.'))  # longitude
        plt.plot(y, x, 'bo')

        if zabka in mozliwe_zabki:
            distance = calculate_distance(client_lat, client_lon, x, y)
            if distance < min_distance:
                min_distance = distance
                nearest_store = zabka

    if nearest_store:
        app.logger.info(f"Nearest store: {nearest_store}")

        #oznaczanie najlbizeszego sklepu spelniajacego wymagania na green
        plt.plot(float(nearest_store['x'].replace(',', '.')), float(nearest_store['y'].replace(',', '.')), 'go', label='Nearest Żabka Store')

    plt.legend()
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.title('Map with żabka store locations')
    plt.grid(True)

    # zapisz wykres do pamieci
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)  # Make sure to seek to the beginning of the file before reading

    #konwertuj obraz na base64
    img_base64 = base64.b64encode(img.getvalue()).decode()

    # Reset the buffer position to the beginning before uploading to blob storage
    img.seek(0)

    # Zapisz obraz do Azure Blob Storage
    blob_name = f"plot_{client['id']}_{nearest_store['id']}.png"
    blob_client = container_client.get_blob_client(blob_name)
    blob_client.upload_blob(img, overwrite=True)

    # URL do obrazu w Azure Blob Storage
    blob_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{container_name}/{blob_name}"
    # Create HTML for display
    html_response = f"""
        <html>
        <head>
            <title>Nearest Store Details</title>
        </head>
        <body>
            <h2>Nearest Store Details:</h2>
            <p><strong>Name:</strong> {nearest_store['nazwa']}</p>
            <p><strong>id:</strong> {nearest_store['id']}</p>
            <p><strong>Distance:</strong> {min_distance:.2f} km</p>
            <h2>Selected Client Details:</h2>
            <p><strong>Client ID:</strong> {client['id']}</p>
            <p><strong>Client Requirements:</strong> {client['wymagania']}</p>
            <h2>Map with żabka store locations:</h2>
            <img src="data:image/png;base64,{img_base64}">
        </body>
        </html>
    """

    return html_response


if __name__ == '__main__':
    app.run(debug=True)
