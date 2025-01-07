import tkinter as tk
from sentinelhub import SHConfig, SentinelHubRequest, DataCollection, MimeType, bbox_to_dimensions, BBox
import numpy as np
import matplotlib.pyplot as plt
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
        self.max_cloud_coverage = 100  # Maksymalne zachmurzenie w procentach

    def download_image(self, bbox, time_interval, resolution=10):
        im_size = bbox_to_dimensions(bbox, resolution=resolution)

        # Evalscript dla oceny zachmurzenia
        evalscript_cloud = """
        function setup() {
            return {
                input: ["CLP"],
                output: { bands: 1 }
            };
        }

        function evaluatePixel(sample) {
            return [sample.CLP];
        }
        """

        # Pobieranie danych z Sentinel Hub z evalscript dla zachmurzenia
        request_cloud = SentinelHubRequest(
            data_folder='data',
            evalscript=evalscript_cloud,
            input_data=[
                SentinelHubRequest.input_data(
                    data_collection=DataCollection.SENTINEL2_L2A,
                    time_interval=time_interval
                )
            ],
            responses=[
                SentinelHubRequest.output_response('default', MimeType.TIFF)
            ],
            bbox=bbox,
            size=im_size,
            config=self.config
        )

        cloud_data = request_cloud.get_data()[0]  # Pobranie danych zachmurzenia
        average_cloud_coverage = np.mean(cloud_data) * 100 / 255.0  # Średnie zachmurzenie w procentach

        if average_cloud_coverage > self.max_cloud_coverage:
            print(f"Odrzucono zdjęcie z zachmurzeniem {average_cloud_coverage:.2f}% (limit: {self.max_cloud_coverage}%)")
            return None, None

        # Evalscript dla wybranego trybu (RGB, NDVI, NDWI, SAVI)
        evalscript_rgb = """
        function setup() {
            return {
                input: ["B04", "B03", "B02"],
                output: { bands: 3 }
            };
        }

        function evaluatePixel(sample) {
            return [2.5 * sample.B04, 2.5 * sample.B03, 2.5 * sample.B02];
        }
        """

        evalscript = evalscript_rgb  # Domyślny tryb RGB
        if self.mode == "NDVI":
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
                let ndwi = (sample.B03 - sample.B08) / (sample.B03 + sample.B08);
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
                let savi = ((sample.B08 - sample.B04) / (sample.B08 + sample.B04 + 0.428)) * 1.428;
                return [savi];
            }
            """

        request_image = SentinelHubRequest(
            data_folder='data',
            evalscript=evalscript,
            input_data=[
                SentinelHubRequest.input_data(
                    data_collection=DataCollection.SENTINEL2_L2A,
                    time_interval=time_interval
                )
            ],
            responses=[
                SentinelHubRequest.output_response('default', MimeType.TIFF)
            ],
            bbox=bbox,
            size=im_size,
            config=self.config
        )

        image = request_image.get_data()[0]
        if self.mode == "RGB":
            return np.clip(image * (2.5 / 200), 0, 1), time_interval
        elif self.mode in ["NDVI", "NDWI", "SAVI"]:
            return np.clip(image / 100, 0, 1), time_interval

    def fetch_least_cloudy_image(self, bbox, time_intervals, resolution=10):
        """
        Iteruje po dostępnych interwałach czasowych, aż znajdzie zdjęcie o dopuszczalnym zachmurzeniu.
        """
        for time_interval in time_intervals:
            image, date_range = self.download_image(bbox, time_interval, resolution)
            if image is not None:
                print(f"Wybrano zdjęcie z daty {date_range} z akceptowalnym zachmurzeniem.")
                return image, date_range
        print("Nie znaleziono zdjęcia z akceptowalnym zachmurzeniem.")
        return None, None

    def save_image(self, image, filename="output_image.tiff"):
        os.makedirs("output", exist_ok=True)
        filepath = os.path.join("output", filename)
        plt.imsave(filepath, image[..., :3], cmap=None)  # Zapisujemy tylko kanały RGB
        print(f"Zdjęcie zapisano jako {filepath}")

    def display_image(self, image, date_range):
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
            ax.imshow(image)
        ax.axis("off")
        ax.set_title(f"Zdjęcie Satelitarne ({self.mode})\nZakres dat: {date_range[0]} - {date_range[1]}", fontsize=14)
        plt.show()


    def set_mode(self, mode):
        self.mode = mode
        print(f"Tryb ustawiony na: {mode}")
