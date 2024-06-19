import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
from azure.cosmos import exceptions, CosmosClient, PartitionKey


# Funkcja do losowania i dopasowywania klientów do żabek
def losuj_i_dopasuj(klienci_df, zabki_df):
    indeks_klienta = np.random.randint(0, len(klienci_df))
    klient = klienci_df.iloc[indeks_klienta]
    print(f"Wybrany klient (indeks {indeks_klienta}):")
    print(klient)

    wymagania = klient['wymagania']
    if wymagania == 'p':
        mozliwe_zabki = zabki_df[zabki_df['punkt_pocztowy'] == 'tak']
    elif wymagania == 'w':
        mozliwe_zabki = zabki_df[zabki_df['wozek'] == 'tak']
    elif wymagania == 'oba':
        mozliwe_zabki = zabki_df[(zabki_df['punkt_pocztowy'] == 'tak') & (zabki_df['wozek'] == 'tak')]
    else:
        mozliwe_zabki = zabki_df

    print(f"Żabki spełniające wymagania klienta '{wymagania}':")
    print(mozliwe_zabki)

    if mozliwe_zabki.empty:
        print("Nie znaleziono żabki spełniającej wymagania klienta.")
        return klient, pd.Series()

    odleglosci = np.sqrt((mozliwe_zabki['x'] - klient['x']) ** 2 + (mozliwe_zabki['y'] - klient['y']) ** 2)
    print("Odległości do żabek:")
    print(odleglosci)

    najblizsza_zabka_idx = odleglosci.idxmin()
    najblizsza_zabka = mozliwe_zabki.loc[najblizsza_zabka_idx]
    print("Najbliższa żabka:")
    print(najblizsza_zabka)

    return klient, najblizsza_zabka


# Wczytanie danych klientów
klienci_df = pd.read_excel("klienci.xlsx")

# Wczytanie danych żabek
zabki_df = pd.read_excel("zabki.xlsx")

# Testowanie funkcji
klient, najblizsza_zabka = losuj_i_dopasuj(klienci_df, zabki_df)

# Wyświetlenie informacji o wylosowanym kliencie i wybranej żabce
print("Wylosowany klient:")
print(klient)
if not najblizsza_zabka.empty:
    print("\nWybrana żabka:")
    print(najblizsza_zabka)
else:
    print("\nNie znaleziono żadnej żabki spełniającej wymagania klienta.")

# Tworzenie mapy
plt.figure(figsize=(10, 8))
plt.scatter(zabki_df['x'], zabki_df['y'], marker='s', color='green', label='Żabki')
plt.scatter(klient['x'], klient['y'], marker='o', color='red', label='Klient')

if not najblizsza_zabka.empty:
    plt.scatter(najblizsza_zabka['x'], najblizsza_zabka['y'], marker='o', color='blue', label='Wybrana żabka')

plt.xlabel('Współrzędna X')
plt.ylabel('Współrzędna Y')
plt.title('Mapa z żabkami i wylosowanym klientem')
plt.legend()
plt.grid(True)
plt.show()

# Zapisanie wybranej żabki do pliku JSON i wysłanie do Azure Cosmos DB
if not najblizsza_zabka.empty:
    zabka_json = {
        "id": str(najblizsza_zabka['id']),
        "nazwa": najblizsza_zabka['nazwa'],
        "x": f"{najblizsza_zabka['x']:.6f}".replace('.', ','),
        "y": f"{najblizsza_zabka['y']:.6f}".replace('.', ','),
        "punkt_pocztowy": najblizsza_zabka['punkt_pocztowy'],
        "wozek": najblizsza_zabka['wozek']
    }

    with open("wybrana_zabka.json", "w", encoding="utf-8") as f:
        json.dump(zabka_json, f, ensure_ascii=False, indent=4)

    print("\nWybrana żabka została zapisana do pliku 'wybrana_zabka.json'")

    # Konfiguracja klienta Azure Cosmos DB
    endpoint = "https://zabka.documents.azure.com:443/"
    key = "S74XazFN5QsBrJKp2FFh1g3X6h3AZefLkEwHQG0IWIZvDRXtC0C1EAIGZsR0vlGq2nPVmB4FILEcACDbdE58Lg=="
    client = CosmosClient(endpoint, key)

    # Tworzenie bazy danych i kolekcji, jeśli nie istnieją
    database_name = 'zabkaDatabase'
    database = client.create_database_if_not_exists(id=database_name)

    container_name = 'zabkaContainer'
    container = database.create_container_if_not_exists(
        id=container_name,
        partition_key=PartitionKey(path="/id"),
        offer_throughput=400
    )

    # Wysłanie danych do Azure Cosmos DB
    container.create_item(body=zabka_json)
    print("\nWybrana żabka została zapisana do Azure Cosmos DB")
else:
    print("\nNie zapisano żadnej żabki, ponieważ nie znaleziono spełniającej wymagania klienta.")
