
import os 
import processing
from qgis.core import QgsRasterLayer, QgsCoordinateReferenceSystem, QgsProject
from glob import glob
import argparse

'''
Script to reproject PNG images (using associated .PGW files) from EPSG:3338 to EPSG:4326, and save the result as a GeoTIFF. This script was used within
the QGIS python console.

Details about QGIS version used, and other dependencies used at the time of using script:

QGIS version - 3.34.12-Prizren
QGIS code revision - 67283536f09
Qt version - 5.15.2
Python version - 3.9.5
GDAL/OGR version - 3.3.2
PROJ version - 8.1.1
EPSG Registry database version - v10.028 (2021-07-07)
GEOS version - 3.9.1-CAPI-1.14.2
SQLite version - 3.35.2
PDAL version - 2.3.0
PostgreSQL client version - unknown
SpatiaLite version - 5.0.1
QWT version - 6.1.6
QScintilla2 version - 2.11.5
OS version - macOS 14.6

Active Python plugins: 
processing - 2.12.99
grassprovider - 2.12.99
db_manager - 0.1.20
MetaSearch - 0.3.6

'''

def reproject_pngs_write_tiffs(dates):

    if isinstance(dates, str):  # If accidentally passed a string, wrap in a list
        dates = [dates]
    elif isinstance(dates, int):  # If accidentally passed an integer, convert to a string inside a list
        dates = [str(dates)]


    for d in dates:
        
        # Adjust source and destination directories based on specific directory hierarchy. 
        source_dir = os.path.join('Users', 'nickcalzada', 'seal', 'data', d, 'created_data', 'edge_pngs_n_pgws')
        dest_dir = os.path.join('Users', 'nickcalzada', 'seal', 'data', d, 'created_data','wgs_84_tifs_from_pngs')
 

        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
        
        png_paths = sorted(glob(os.path.join(source_dir, '*.png')))
        print(png_paths)
        
        for png_path in png_paths[:]:
            
            filename = png_path.split('/')[-1].split('.')[0]
            filename = filename + '.tif'
            output_path = os.path.join(dest_dir, filename)

            # Load the PNG image as a raster layer
            layer = QgsRasterLayer(png_path, "My Image")

            # Check if the layer is valid
            if not layer.isValid():
                print("Layer failed to load. Make sure the file path is correct and the image is georeferenced.")
            else:
                # Set the CRS of the layer to EPSG:4326 (before reprojection)
                layer.setCrs(QgsCoordinateReferenceSystem("EPSG:3338"))

                # Reproject the layer to EPSG:4326 and save as a GeoTIFF with nearest neighbor resampling
                parameters = {
                    'INPUT': layer,
                    'SOURCE_CRS': 'EPSG:3338', 
                    'TARGET_CRS': 'EPSG:4326',
                    'OUTPUT': output_path,
                    'FORMAT': 'GTiff',
                    'RESAMPLING': 0,  # Nearest neighbor resampling
                    'NO_DATA': 0 
                }
                
                # Run the processing algorithm
                processing.run("gdal:warpreproject", parameters)
                print("Reprojection complete. Output saved to:", output_path)

        print('Done converting edge jpgs to wgs 84 geotiffs!')


if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Reproject tifs to WGS84 CRS.')
    parser.add_argument('-d', '--dates', required = True, help = 'Survey date(s) of interest.')
    args = parser.parse_args()
    reproject_pngs_write_tiffs(dates = args.dates)
    
        