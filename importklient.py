import pandas as pd
import json
from azure.cosmos import CosmosClient, exceptions, PartitionKey

# Dane połączenia do Azure Cosmos DB
endpoint = "https://zabka.documents.azure.com:443/"
key = "S74XazFN5QsBrJKp2FFh1g3X6h3AZefLkEwHQG0IWIZvDRXtC0C1EAIGZsR0vlGq2nPVmB4FILEcACDbdE58Lg=="
database_name = 'zabkaDatabase'
container_name = 'klientContainer'

# Konfiguracja klienta Cosmos DB
client = CosmosClient(endpoint, key)
database = client.create_database_if_not_exists(id=database_name)
container = database.create_container_if_not_exists(
    id=container_name,
    partition_key=PartitionKey(path="/id"),
    offer_throughput=400
)

# Funkcja do wstawiania dokumentów do Cosmos DB
def insert_document_to_cosmos(container, document):
    try:
        container.create_item(body=document)
    except exceptions.CosmosResourceExistsError:
        print(f"Document with id {document['id']} already exists in the database.")
    except exceptions.CosmosHttpResponseError as e:
        print(f"An error occurred: {e.message}")

# Odczytanie danych z pliku Excel
file_path = 'klienci.xlsx'  # Upewnij się, że plik jest w odpowiednim katalogu
df = pd.read_excel(file_path)

# Iteracja po wierszach i importowanie danych do Cosmos DB
for index, row in df.iterrows():
    document = {
        "id": str(row['id']),
        "x": str(row['x']),
        "y": str(row['y']),
        "wymagania": row['wymagania'],
    }
    insert_document_to_cosmos(container, document)
    print(f"Inserted document with id {document['id']}")
