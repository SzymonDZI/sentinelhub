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

    def download_image(self, bbox, time_interval, resolution=60):
        size = bbox_to_dimensions(bbox, resolution=resolution)

        request = SentinelHubRequest(
            data_folder='data',
            evalscript="""
            function setup() {
                return {
                    input: ["B04", "B03", "B02"],
                    output: { bands: 3 }
                };
            }
            function evaluatePixel(sample) {
                return [sample.B04, sample.B03, sample.B02];
            }
            """,
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
            size=size,
            config=self.config
        )

        image = request.get_data()[0]
        return np.clip(image / 3000, 0, 1)

    def save_image(self, image, filename="output_image.tiff"):
        os.makedirs("output", exist_ok=True)
        filepath = os.path.join("output", filename)
        plt.imsave(filepath, image)
        print(f"Zdjęcie zapisano jako {filepath}")

    def display_image(self, image):
        plt.figure(figsize=(10, 10))
        plt.imshow(image)
        plt.axis("off")
        plt.title("Zdjęcie Satelitarne (Kolory Naturalne)")
        plt.show()
