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
import matplotlib.colors as mcolors
from matplotlib.colors import to_rgba
from scipy.spatial import KDTree

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
                return [sample.B04, sample.B03, sample.B02];
            }
            """
        elif self.mode == "NDVI":
            evalscript = """
            //VERSION=3
            function setup() {
            return {
                input: ["B04", "B08", "dataMask"],
                output: { bands: 4 }
            };
            }

            const ramp = [
            [-0.5, 0x0c0c0c],
            [-0.2, 0xbfbfbf],
            [-0.1, 0xdbdbdb],
            [0, 0xeaeaea],
            [0.025, 0xfff9cc],
            [0.05, 0xede8b5],
            [0.075, 0xddd89b],
            [0.1, 0xccc682],
            [0.125, 0xbcb76b],
            [0.15, 0xafc160],
            [0.175, 0xa3cc59],
            [0.2, 0x91bf51],
            [0.25, 0x7fb247],
            [0.3, 0x70a33f],
            [0.35, 0x609635],
            [0.4, 0x4f892d],
            [0.45, 0x3f7c23],
            [0.5, 0x306d1c],
            [0.55, 0x216011],
            [0.6, 0x0f540a],
            [1, 0x004400],
            ];

            const visualizer = new ColorRampVisualizer(ramp);

            function evaluatePixel(samples) {
            let ndvi = index(samples.B08, samples.B04);
            let imgVals = visualizer.process(ndvi);
            return imgVals.concat(samples.dataMask);
            }

            """
        elif self.mode == "NDWI":
            evalscript = """
            //VERSION=3
            //ndwi
            const colorRamp1 = [
                [0, 0xFFFFFF],
                [1, 0x008000]
            ];
            const colorRamp2 = [
                [0, 0xFFFFFF],
                [1, 0x0000CC]
            ];

            let viz1 = new ColorRampVisualizer(colorRamp1);
            let viz2 = new ColorRampVisualizer(colorRamp2);

            function setup() {
            return {
                input: ["B03", "B08", "SCL","dataMask"],
                output: [
                    { id:"default", bands: 4 },
                    { id: "index", bands: 1, sampleType: "FLOAT32" },
                    { id: "eobrowserStats", bands: 2, sampleType: 'FLOAT32' },
                    { id: "dataMask", bands: 1 }
                ]
            };
            }

            function evaluatePixel(samples) {
            let val = index(samples.B03, samples.B08);
            let imgVals = null;
            // The library for tiffs works well only if there is only one channel returned.
            // So we encode the "no data" as NaN here and ignore NaNs on frontend.
            const indexVal = samples.dataMask === 1 ? val : NaN;
            
            if (val < -0) {
                imgVals = [...viz1.process(-val), samples.dataMask];
            } else {
                imgVals = [...viz2.process(Math.sqrt(Math.sqrt(val))), samples.dataMask];
            }
            return {
                default: imgVals,
                index: [indexVal],
                eobrowserStats:[val,isCloud(samples.SCL)?1:0],
                dataMask: [samples.dataMask]
            };
            }


            function isCloud(scl) {
            if (scl == 3) {
                // SC_CLOUD_SHADOW
                return false;
            } else if (scl == 9) {
                // SC_CLOUD_HIGH_PROBA
                return true;
            } else if (scl == 8) {
                // SC_CLOUD_MEDIUM_PROBA
                return true;
            } else if (scl == 7) {
                // SC_CLOUD_LOW_PROBA
                return false;
            } else if (scl == 10) {
                // SC_THIN_CIRRUS
                return true;
            } else if (scl == 11) {
                // SC_SNOW_ICE
                return false;
            } else if (scl == 1) {
                // SC_SATURATED_DEFECTIVE
                return false;
            } else if (scl == 2) {
                // SC_DARK_FEATURE_SHADOW
                return false;
            }
            return false;
            }


            """
        elif self.mode == "SAVI":
            evalscript = """
            // Soil Adjusted Vegetation Index  (abbrv. SAVI)
            // General formula: (800nm - 670nm) / (800nm + 670nm + L) * (1 + L)
            // URL https://www.indexdatabase.de/db/si-single.php?sensor_id=96&rsindex_id=87
            function setup() {
            return {
                input: ["B04", "B08", "dataMask"],
                output: { bands: 4 }
            };
            }

            let L = 0.428; // L = soil brightness correction factor could range from (0 -1)

            const ramp = [
            [-0.5, 0x0c0c0c],
            [-0.2, 0xbfbfbf],
            [-0.1, 0xdbdbdb],
            [0, 0xeaeaea],
            [0.025, 0xfff9cc],
            [0.05, 0xede8b5],
            [0.075, 0xddd89b],
            [0.1, 0xccc682],
            [0.125, 0xbcb76b],
            [0.15, 0xafc160],
            [0.175, 0xa3cc59],
            [0.2, 0x91bf51],
            [0.25, 0x7fb247],
            [0.3, 0x70a33f],
            [0.35, 0x609635],
            [0.4, 0x4f892d],
            [0.45, 0x3f7c23],
            [0.5, 0x306d1c],
            [0.55, 0x216011],
            [0.6, 0x0f540a],
            [1, 0x004400],
            ];

            const visualizer = new ColorRampVisualizer(ramp);

            function evaluatePixel(samples) {
            const index = (samples.B08 - samples.B04) / (samples.B08 + samples.B04 + L) * (1.0 + L);
            let imgVals = visualizer.process(index);
            return imgVals.concat(samples.dataMask)
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
        # Zdefiniuj punkty normalizacji NDVI
        original_values = np.array([-0.5, -0.2, -0.1, 0, 0.025, 0.05, 0.075, 0.1, 0.125, 0.15, 
                                    0.175, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 1])
        normalized_values = (original_values - original_values.min()) / (original_values.max() - original_values.min())

        # Zdefiniuj kolory odpowiadające wartościom NDVI
        colors = [
            "#0c0c0c", "#bfbfbf", "#dbdbdb", "#eaeaea", "#fff9cc", "#ede8b5", "#ddd89b", 
            "#ccc682", "#bcb76b", "#afc160", "#a3cc59", "#91bf51", "#7fb247", "#70a33f", 
            "#609635", "#4f892d", "#3f7c23", "#306d1c", "#216011", "#0f540a", "#004400"
        ]

        # Przeskaluj wartości NDVI do zakresu [0, 1]
        normalized_values = (original_values - original_values.min()) / (original_values.max() - original_values.min())

        # Tworzenie mapy kolorów z przeskalowanymi wartościami
        cmap_ndvi = mcolors.LinearSegmentedColormap.from_list("custom_ndvi", list(zip(normalized_values, colors)))

        # Norma w zakresie -0.5 do 1 (dla poprawnego odwzorowania danych wejściowych)
        norm_ndvi = mcolors.Normalize(vmin=-0.5, vmax=1)

        # Zdefiniuj rampę kolorów dla NDWI i przeskaluj wartości na zakres [0, 1]
        original_values = np.array([-0.8, 0, 0.8])  # Oryginalny zakres NDWI
        normalized_values = (original_values - original_values.min()) / (original_values.max() - original_values.min())  # Skalowanie do [0, 1]
        ndwi_colors = ["#008000", "#FFFFFF", "#0000FF"]  

        # Tworzenie mapy kolorów i normy
        cmap_ndwi = mcolors.LinearSegmentedColormap.from_list("custom_ndwi", list(zip([0, 0.5, 1], ndwi_colors)))
        norm_ndwi = mcolors.Normalize(vmin=-0.8, vmax=0.8)

        # Zdefiniuj rampy kolorów dla różnych indeksów
        original_values = np.array([-0.5, -0.2, -0.1, 0, 0.025, 0.05, 0.075, 0.1, 0.125, 0.15, 
                                0.175, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 1])
        savi_colors = [
            "#0c0c0c", "#bfbfbf", "#dbdbdb", "#eaeaea", "#fff9cc", "#ede8b5", "#ddd89b", 
            "#ccc682", "#bcb76b", "#afc160", "#a3cc59", "#91bf51", "#7fb247", "#70a33f", 
            "#609635", "#4f892d", "#3f7c23", "#306d1c", "#216011", "#0f540a", "#004400"
        ]

        # Normalizacja wartości SAVI do zakresu [0, 1]
        normalized_values = (original_values - original_values.min()) / (original_values.max() - original_values.min())

        # Tworzenie mapy kolorów z przeskalowanymi wartościami
        cmap_savi = mcolors.LinearSegmentedColormap.from_list("custom_savi", list(zip(normalized_values, savi_colors)))

        # Norma dla SAVI w zakresie rzeczywistych wartości (-0.5 do 1)
        norm_savi = mcolors.Normalize(vmin=-0.5, vmax=1)

        # Sprawdź wymiary obrazu
        height, width, _ = image.shape if len(image.shape) == 3 else (image.shape[0], image.shape[1], 1)

        if height != width:
            # Dodaj marginesy, aby zrobić obraz kwadratowy
            size = min(height, width)
            start_y = (height - size) // 2
            start_x = (width - size) // 2
            image = image[start_y:start_y + size, start_x:start_x + size]

        # Tworzenie mapowania kolor -> wartość
        rgba_colors = np.array([to_rgba(color) for color in colors])  # Kolory w RGBA
        kdtree = KDTree(rgba_colors)  # Struktura KDTree dla szybkiego wyszukiwania
        
        def find_closest_value(pixel_color):
            """Znajdź najbliższy kolor i zwróć odpowiadającą mu wartość."""
            distance, index = kdtree.query(pixel_color)  # Znajdź najbliższy kolor
            return original_values[index]
        
        def on_mouse_click(event):
            if event.inaxes == ax:
                x, y = int(event.xdata), int(event.ydata)
                if 0 <= x < image.shape[1] and 0 <= y < image.shape[0]:
                    if self.mode in ["NDVI", "SAVI"]:
                        # Pobierz kolor piksela w formacie RGBA
                        pixel_color = to_rgba(image[y, x])
                        
                        # Znajdź najbliższą wartość dla koloru
                        value = find_closest_value(pixel_color)
                        label = f"{self.mode}: {value:.3f}"
                    else:
                        label = "Tryb RGB"
                    
                    # Aktualizacja tekstu
                    text.set_text(label)
                    fig.canvas.draw_idle()

        # Wyświetl obraz z legendą
        fig, ax = plt.subplots(figsize=(10, 10))

        if self.mode == "NDVI":
            cax = ax.imshow(image, cmap=cmap_ndvi, norm=norm_ndvi)
            cbar = fig.colorbar(cax, ax=ax, orientation='vertical', shrink=0.8, pad=0.05)
            cbar.set_label("NDVI wartość", fontsize=12)
        elif self.mode == "NDWI":
            cax = ax.imshow(image, cmap=cmap_ndwi, norm=norm_ndwi)
            cbar = fig.colorbar(cax, ax=ax, orientation='vertical', shrink=0.8, pad=0.05)
            cbar.set_label("NDWI wartość", fontsize=12)
        elif self.mode == "SAVI":
            cax = ax.imshow(image, cmap=cmap_savi, norm=norm_savi)
            cbar = fig.colorbar(cax, ax=ax, orientation='vertical', shrink=0.8, pad=0.05)
            cbar.set_label("SAVI wartość", fontsize=12)
        else:
            ax.imshow(image, cmap='viridis')

        ax.axis("off")
        timestamp = timestamp.replace("T", " ").replace("Z", "")
        ax.set_title(f"Zdjęcie Satelitarne ({self.mode})\nZdjęcie wykonano: {timestamp}", fontsize=14)
        # Dodanie dynamicznego wyświetlania wartości wskaźnika
        text = ax.text(0.95, 0.05, "", transform=ax.transAxes, fontsize=12,
                       color="black", ha="right", va="bottom", bbox=dict(facecolor='white', alpha=0.5))
        
        # Obsługa kliknięcia myszą
        fig.canvas.mpl_connect("button_press_event", on_mouse_click)
        plt.show()

    def set_mode(self, mode):
        self.mode = mode
        print(f"Tryb ustawiony na: {mode}")