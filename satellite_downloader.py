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
                return [2.5 * sample.B04, 2.5 * sample.B03, 2.5 * sample.B02];
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
                SentinelHubRequest.output_response('default', MimeType.TIFF)
            ],
            bbox=bbox,
            size=im_size,
            config=self.config
        )

        image = request.get_data()[0]
        if self.mode == "RGB":
            return np.clip(image * (2.5 / 200), 0, 1), time_interval
        elif self.mode == "NDVI":
            return np.clip(image, 0, 1), time_interval

    def save_image(self, image, filename="output_image.tiff"):
        os.makedirs("output", exist_ok=True)
        filepath = os.path.join("output", filename)
        plt.imsave(filepath, image, cmap="RdYlGn" if self.mode == "NDVI" else None)
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

        # Wyświetl obraz
        plt.figure(figsize=(10, 10))
        plt.imshow(image, cmap="RdYlGn" if self.mode == "NDVI" else None)
        plt.axis("off")
        plt.title("Zdjęcie Satelitarne ({})".format("NDVI" if self.mode == "NDVI" else "Kolory Naturalne"))
        plt.show()

    def set_mode(self, mode):
        self.mode = mode
        print(f"Tryb ustawiony na: {mode}")