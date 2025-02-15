from sentinelhub import (
    SHConfig,
    CRS,
    BBox,
    DataCollection,
    MimeType,
    MosaickingOrder,
    SentinelHubRequest,
    bbox_to_dimensions
)
import numpy as np
import matplotlib.pyplot as plt

# Konfiguracja Sentinel Hub
config = SHConfig()
config.instance_id = 'd6d1603e-a6f9-407f-b473-90214c91d379'
config.sh_client_id = 'b293465d-c7a1-4065-8257-b68bd1812d9b'
config.sh_client_secret = 'NDhVObKWLQr4CdVuJYgCWn9yCEYQXeHF'

# Pobranie indeksu pasma
print("Podaj wartości od 0 do 12, odpowiadające pasmom:")
input_values = input("Wprowadź liczby: ")

try:
    band_index = [int(value) for value in input_values.split() if 1 <= int(value) <= 12]
    if not band_index:
        print("Nie wprowadzono żadnych poprawnych wartości z zakresu 0-12.")
        exit()
    else:
        print(f"Wprowadzone wartości: {band_index}")
        #band_index = [(band_index[0] - band_index[1]) / (band_index[0] + band_index[1])]
        #print(band_index)
        band_index_value = int(band_index[0])  # Obliczona wartość indeksu pasma
except ValueError:
    print("Wprowadź tylko liczby całkowite, oddzielone spacjami.")
    exit()

# Definicja współrzędnych i rozdzielczości
betsiboka_coords_wgs84 = (46.16, -16.15, 46.51, -15.58)
resolution = 60
bbox = BBox(bbox=betsiboka_coords_wgs84, crs=CRS.WGS84)
size = bbox_to_dimensions(bbox, resolution=resolution)

# Pobranie danych Sentinel-2
evalscript_all_bands = """
    //VERSION=3
    function setup() {
        return {
            input: [{
                bands: ["B01","B02","B03","B04","B05","B06","B07","B08","B8A","B09","B10","B11","B12"],
                units: "DN"
            }],
            output: {
                bands: 13,
                sampleType: "INT16"
            }
        };
    }

    function evaluatePixel(sample) {
        return [sample.B01, // 0
                sample.B02, // 1
                sample.B03, // 2
                sample.B04, // 3
                sample.B05, // 4
                sample.B06, // 5
                sample.B07, // 6
                sample.B08, // 7
                sample.B8A, // 8
                sample.B09, // 9
                sample.B10, // 10
                sample.B11, // 11
                sample.B12]; // 12
    }
"""

request_all_bands = SentinelHubRequest(
    evalscript=evalscript_all_bands,
    input_data=[
        SentinelHubRequest.input_data(
            data_collection=DataCollection.SENTINEL2_L1C,
            time_interval=("2020-06-01", "2020-06-30"),
            mosaicking_order=MosaickingOrder.LEAST_CC,
        )
    ],
    responses=[SentinelHubRequest.output_response("default", MimeType.TIFF)],
    bbox=bbox,
    size=size,
    config=config,
)

all_bands_response = request_all_bands.get_data()

factor = 3.5 / 1e4
image = all_bands_response[0][:, :, band_index] * factor #dla zbioru masek

plt.figure(figsize=(10, 10))
plt.imshow(image, cmap="viridis", vmax=1)
plt.title(f"Kompozycja barwna, rozdzielczość {resolution} m")
plt.axis("off")
plt.show()
