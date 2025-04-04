import os
from rasterio.features import geometry_mask
from shapely.geometry import Polygon
import geopandas as gpd
import rasterio
import numpy as np 
from glob import glob
from tqdm import tqdm
import pandas as pd 
import argparse

def find_ice_props(filled_in_tiff_path, polygons):
    
    '''
    Using the filled GeoTIFFs and associated grid cells (polygons gathered in steps 0-1), calculate the proportion of each cell covered by ice. 
    '''

    with rasterio.open(filled_in_tiff_path) as src:
        if polygons.crs != src.crs:
            polygons = polygons.to_crs(src.crs)
        
        filled_iceberg = src.read(1)    
        pixel_area = src.res[0] * src.res[1]
        ice_proportions = []

        polygons.loc[:, 'python_area'] = polygons.geometry.area
        
        for idx, poly in enumerate(polygons.geometry[:]):

            # Logical mask denoting where the polygon and image align
            mask = geometry_mask([poly], transform=src.transform, invert=True, out_shape=src.shape)         
            
            # Find the sum of where they overlap times pixel area                                                                                                                                   
            ice_area = (filled_iceberg & mask).sum() * pixel_area
            total_area = polygons.loc[idx, 'python_area']
            proportion_ice = ice_area /  total_area
            ice_proportions.append(proportion_ice)
        
        # save ice proportion values as new 'z' column and save the final df 
        polygons.loc[:, 'z'] = ice_proportions
        final_df = polygons[['geometry', 'area', 'python_area', 'x', 'y', 'z']]
    
    return final_df

####################################################################################################
def find_ice_props_many_imgs(filled_in_tiff_paths, polygon_df):
    
    '''
    Perform ice proportion calculations on whole survey dates at once. 
    '''
    
    survey_data = []
    filled_in_tiff_paths_sub = sorted(filled_in_tiff_paths)

    for i, filled_in_tiff in tqdm(enumerate(sorted(filled_in_tiff_paths_sub))):
        
        print(f'\n\nworking on {filled_in_tiff.split('/')[-1]} \n')
        
        # name structure of jpg images (unique key in the polygon df) = JHI_20070813_xxxx.JPG
        name = filled_in_tiff.split('/')[-1].replace('filled_', '').replace('_iceberg_edges.tif', '.JPG')
        
        # polygon_subset = polygon_df[polygon_df['file_name'] == name]            
        polygon_subset = polygon_df[polygon_df['file_name'] == name].reset_index(drop=True)

        img_iter = find_ice_props(filled_in_tiff_path=filled_in_tiff, polygons=polygon_subset)
        survey_data.append(img_iter)
        
    if survey_data:
        combined_gdf = gpd.GeoDataFrame(pd.concat(survey_data, ignore_index=True))
        return combined_gdf
    
    else:
        print("No data to concatenate.")
        return gpd.GeoDataFrame() 

# MAIN ###################################################################################################
if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Find proportion of ice in each grid cell using associated shapefiles')
    parser.add_argument('-f', '--filled', required = True, help = 'Path to source directory of filled-in binary tiffs')
    parser.add_argument('-p', '--poly_df', required = True, help = 'Path to directory containing grid cell polygon shapefiles')
    parser.add_argument('-n', '--name', required = True, help = 'Name of output CSV file for geopandas dataframe containing cell centers and ice proportions')
    args = parser.parse_args()
    print(args)
    
    if not args.name.endswith('.csv'):
        raise ValueError('Invalid output name format. CSV format required.')
        
    filled_in_tiffs = glob(os.path.join(args.filled, '*.tif'))
    polygon_df = gpd.read_file(args.poly_df)
    
    gdf = find_ice_props_many_imgs(filled_in_tiff_paths=filled_in_tiffs, polygon_df=polygon_df)
    gdf.to_csv(args.name, mode = 'w')

