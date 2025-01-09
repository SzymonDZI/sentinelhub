from sentinelhub import (
    SHConfig,
    CRS,
    BBox,
    DownloadRequest,
    DataCollection,
    MimeType,
    MosaickingOrder,
    SentinelHubRequest,
    SentinelHubCatalog,
    SentinelHubDownloadClient,
    bbox_to_dimensions
)
import numpy as np
import matplotlib.pyplot as plt
from utils import plot_image
import os

class SatelliteDataDownloader:
    def __init__(self, instance_id, client_id, client_secret):
        self.config = SHConfig()
        self.config.instance_id = instance_id
        self.config.sh_client_id = client_id
        self.config.sh_client_secret = client_secret

        if not self.config.instance_id or not self.config.sh_client_id or not self.config.sh_client_secret:
            raise ValueError("Instance ID, Client ID, lub Client Secret są nieprawidłowe.")

        self.mode = "RGB"  # Domyślny tryb

    def get_image_metadata(self, bbox, time_interval):
        catalog = SentinelHubCatalog(self.config)
        search_iterator = catalog.search(
            DataCollection.SENTINEL2_L2A,
            bbox=BBox(bbox, CRS.WGS84),
            time=time_interval,
            filter="eo:cloud_cover < 100",
            fields={"include": ["id", "properties.datetime", "properties.eo:cloud_cover"], "exclude": []},
        )
        metadata = list(search_iterator)
        if not metadata:
            raise ValueError("Nie znaleziono żadnych danych dla podanych parametrów.")
        return metadata
    
    def download_image(self, bbox, time_interval, resolution=10):
        im_size = bbox_to_dimensions(bbox, resolution=resolution)
        
        if self.mode == "RGB":
            evalscript = """
            function setup() {
                return {
                    input: ["B04", "B03", "B02"],
                    output: { bands: 3 }
                };
            }
            function evaluatePixel(sample) {
                return [1 * sample.B04, 1 * sample.B03, 1 * sample.B02];
            }
            """
        elif self.mode == "NDVI":
            evalscript = """
            function setup() {
                return {
                    input: ["B08", "B04"],
                    output: { bands: 1 }
                };
            }
            function evaluatePixel(sample) {
                let ndvi = (sample.B08 - sample.B04) / (sample.B08 + sample.B04);
                return [ndvi];
            }
            """
        elif self.mode == "NDWI":
            evalscript = """
            function setup() {
                return {
                    input: ["B03", "B08"],
                    output: { bands: 1 }
                };
            }
            function evaluatePixel(sample) {
                let ndwi = (1.5 * sample.B03 - sample.B08) / (sample.B03 + 1.5 * sample.B08);
                return [ndwi];
            }
            """
        elif self.mode == "SAVI":
            evalscript = """
            function setup() {
                return {
                    input: ["B08", "B04"],
                    output: { bands: 1 }
                };
            }
            function evaluatePixel(sample) {
                let savi = ((sample.B08 - sample.B04) / (sample.B08 + sample.B04 + 0.5)) * 1.5;
                return [savi];
            }
            """
        request = SentinelHubRequest(
            data_folder='data',
            evalscript=evalscript,
            input_data=[
                SentinelHubRequest.input_data(
                    data_collection=DataCollection.SENTINEL2_L2A,
                    time_interval=time_interval,
                    other_args={"dataFilter": {"mosaickingOrder": "leastCC"}}

                )
            ],
            responses=[
                SentinelHubRequest.output_response('default', MimeType.TIFF),
            ],
            bbox=bbox,
            size=im_size,
            config=self.config
        )

        
        metadata = self.get_image_metadata(bbox, time_interval)
        print(metadata)
        # Znajdowanie elementu z najmniejszym zachmurzeniem
        best_metadata = min(metadata, key=lambda x: x['properties']['eo:cloud_cover'])
        # Pobieranie daty i czasu
        timestamp = best_metadata['properties']['datetime']
        print(f"Zdjęcie wykonano: {timestamp}")
        image = request.get_data()
        factor = request.get_data()
        print(image[0].shape)
        print(image[0][1][1])
        if self.mode == "RGB":
            return np.clip(image[0] * (2.5 / 200), 0, 1), time_interval, timestamp
        elif self.mode in ["NDVI", "NDWI", "SAVI"]:
            return np.clip(image[0] / 200, 0, 1), time_interval, timestamp
        
    def save_image(self, image, filename="output_image.tiff"):
        os.makedirs("output", exist_ok=True)
        filepath = os.path.join("output", filename)
        plt.imsave(filepath, image, cmap="RdYlGn" if self.mode == "NDVI" else None)
        print(f"Zdjęcie zapisano jako {filepath}")

    def display_image(self, image, date_range, timestamp):
        # Sprawdź wymiary obrazu
        height, width, _ = image.shape if len(image.shape) == 3 else (image.shape[0], image.shape[1], 1)

        if height != width:
            # Dodaj marginesy, aby zrobić obraz kwadratowy
            size = min(height, width)
            start_y = (height - size) // 2
            start_x = (width - size) // 2
            image = image[start_y:start_y + size, start_x:start_x + size]


        # Wyświetl obraz z legendą
        fig, ax = plt.subplots(figsize=(10, 10))
        if self.mode in ["NDVI", "NDWI", "SAVI"]:
            cmap = "RdYlGn" if self.mode == "NDVI" else "Blues" if self.mode == "NDWI" else "YlGn"
            cax = ax.imshow(image, cmap=cmap)
            cbar = fig.colorbar(cax, ax=ax, orientation='vertical', shrink=0.8, pad=0.05)
            cbar.set_label(f"{self.mode} wartość", fontsize=12)
        else:
            ax.imshow(image, cmap='viridis')
        ax.axis("off")
        timestamp = timestamp.replace("T", " ").replace("Z", "")
        ax.set_title(f"Zdjęcie Satelitarne ({self.mode})\nZdjęcie wykonano: {timestamp}", fontsize=14)
        plt.show()


    def set_mode(self, mode):
        self.mode = mode
        print(f"Tryb ustawiony na: {mode}")