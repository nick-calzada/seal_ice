from step_5_fill_tiffs import * 
from step_6_calc_ice_props import *
#from step_7_make_ice_prop_skeletons import make_skeleton
import argparse
import os 
import geopandas as gpd 

if __name__ == '__main__':    
    parser = argparse.ArgumentParser(description='Enter survey date(s) to fill in iceberg tiff files, calculate ice proprotions within each grid cell, and create an output dataframe with ice proportions for every cell.')
    parser.add_argument('-d', '--dates', nargs = '+', required = True, help = 'Survey date(s) of interest.')
    args = parser.parse_args()
    # dates = args.dates
    # print(dates)
    
    for d in args.dates:

        # 1. Fill in and write tiffs 
        print(f'\nFilling in icebergs for survey date {d}...\n')
        edge_tiff_path = os.path.join('/Users/nickcalzada/seal/data', str(d), 'created_data', 'wgs_84_edge_tifs_from_pngs')
        edge_tifs = glob(os.path.join(edge_tiff_path, '*.tif'))
        output_dir = os.path.join('/Users/nickcalzada/seal/data', str(d), 'created_data', 'filled_tiffs')
        for edge_tif in tqdm(edge_tifs):
            fill_and_write_tiff(edge_tiff_path=edge_tif, output_dir=output_dir)
            # fill_and_write_tiff(edge_tiff_path=edge_tiff_path, output_dir=output_dir)

        # 2. Calculate ice proportions 
        print(f'\nCalculating ice proportions for survey date {d}...\n')
        filled_tiffs_path = output_dir
        filled_in_tiffs = glob(os.path.join(filled_tiffs_path, '*.tif'))
        # print(filled_in_tiffs)
        poly_df_name = f'{d}_grid_cells.shp'
        poly_file = os.path.join('grid_cells_20070618_SB', poly_df_name) # Change depending on where the shapefiles are located
        poly_df = gpd.read_file(poly_file)
        # print(poly_df)

        gdf = find_ice_props_many_imgs(filled_in_tiff_paths=filled_in_tiffs, polygon_df=poly_df)
        # gdf = find_ice_props_many_imgs(filled_in_tiff_paths=filled_in_tiffs, polygon_df=polygon_df)
        file_name = f'ice_props_{d}.csv'
        df_name = os.path.join('final_ice_props_w_one_sb', file_name)
        gdf.to_csv(df_name, mode = 'w')
        
        # 3. Make skeleton dataframe with observed and unobserved proprotions and cell coordinates. 
        # make_skeleton(survey=d)






    
    
    
#    if not args.name.endswith('.csv'):
 #       raise ValueError('Invalid output name format. CSV format required.')
       
