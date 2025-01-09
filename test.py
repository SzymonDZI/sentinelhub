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
from utils import plot_image

class SentinelDataFetcher:
    def __init__(self, instance_id, client_id, client_secret):
        self.config = SHConfig()
        self.config.instance_id = instance_id
        self.config.sh_client_id = client_id
        self.config.sh_client_secret = client_secret
        self.selected_coords = None

    def get_band_index(self):
        """Prompt user for band index input and return the result."""
        print("Podaj wartości (od 1 do 12), oddzielone spacją:")
        input_values = input("Wprowadź liczby: ")

        try:
            # Konwersja danych wejściowych na listę liczb całkowitych
            band_index = [int(value) for value in input_values.split() if 1 <= int(value) <= 12]
            
            if not band_index:
                print("Nie wprowadzono żadnych poprawnych wartości z zakresu 1-12.")
                return None
            else:
                print(f"Wprowadzone wartości: {band_index}")
                band_index = [(band_index[0] - band_index[1]) / (band_index[0] + band_index[1])]
                print(band_index)
                return int(band_index[0])  # Return integer value after calculation
        except ValueError:
            print("Wprowadź tylko liczby całkowite, oddzielone spacjami.")
            return None

    def get_bbox_and_size(self, coords_wgs84, resolution):
        """Create a bounding box and calculate image size based on resolution."""
        bbox = BBox(bbox=coords_wgs84, crs=CRS.WGS84)
        size = bbox_to_dimensions(bbox, resolution=resolution)
        return bbox, size

    def fetch_data(self, bbox, size):
        """Fetch the Sentinel-2 image data for the given bounding box and size."""
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
                return [sample.B01,
                        sample.B02,
                        sample.B03,
                        sample.B04,
                        sample.B05,
                        sample.B06,
                        sample.B07,
                        sample.B08,
                        sample.B8A,
                        sample.B09,
                        sample.B10,
                        sample.B11,
                        sample.B12];
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
            config=self.config,
        )

        return request_all_bands.get_data()

    def plot_image(self, image, resolution, factor):
        """Plot the image with a specific colormap and colorbar."""
        plt.figure(figsize=(10, 10))
        plt.imshow(image, cmap="viridis", vmax=1)
        plt.colorbar(label="SWIR Band Intensity")
        plt.title(f"{resolution} m Resolution")
        plt.axis("off")
        plt.show()

    def process_image(self, band_index, coords_wgs84, resolution=60):
        """Main method to process and display Sentinel-2 data."""
        band_index_value = self.get_band_index()
        if band_index_value is None:
            return

        bbox, size = self.get_bbox_and_size(coords_wgs84, resolution)
        all_bands_response = self.fetch_data(bbox, size)

        # Wizualizacja obrazu dla pasma SWIR (B12)
        # Factor 1/1e4 ze względu na zakres wartości DN w zakresie 0-10000
        # Factor 3.5 zwiększa jasność
        factor = 3.5 / 1e4
        image = all_bands_response[0][:, :, band_index_value] * factor

        self.plot_image(image, resolution, factor)


# Użycie klasy
if __name__ == "__main__":
    fetcher = SentinelDataFetcher(
        instance_id='f66014dd-14a9-4807-82cc-b188ac4b05ff',
        client_id='df508090-1f72-49ec-a554-2ac1f63a8ec3',
        client_secret='gvd666chE5OzcwVNOYaznG7slRu4GO2A'
    )

    # Przykładowe współrzędne i rozdzielczość
    betsiboka_coords_wgs84 = (46.16, -16.15, 46.51, -15.58)
    fetcher.process_image(band_index=12, coords_wgs84=betsiboka_coords_wgs84, resolution=60)
