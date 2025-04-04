import os 
import rasterio
from rasterio.plot import show
#import matplotlib.pyplot as plt
import numpy as np
import cv2
from glob import glob
from tqdm import tqdm
import argparse

# 1. Fill in iceberg boundaries #############################################################################
def flood_fill_with_boundaries(edges):
    
    '''
    Function to perform a floodfill on the binary iceberg outline GeoTIFFs.
    '''
    
    filled = edges.astype(np.uint8)
    boundary_mask = (filled == 255)
    
    # Find a seed point that is not on a boundary edge.
    seed_point = None
    for x in range(filled.shape[1]):  # top and bottom row
        if filled[0, x] == 0:
            seed_point = (x, 0)
            break
        if filled[-1, x] == 0:
            seed_point = (x, filled.shape[0] - 1)
            break
    if seed_point is None:  
        for y in range(filled.shape[0]): # left and right columns
            if filled[y, 0] == 0:
                seed_point = (0, y)
                break
            if filled[y, -1] == 0:
                seed_point = (filled.shape[1] - 1, y)
                break

    if seed_point is not None:
        
        # Fill in background to be able to distinguish between in and outside of boundaries        
        # 	cv.floodFill(	image, mask, seedPoint, newVal[, loDiff[, upDiff[, flags]]]	) -> retval, image, mask, rect
        
        _, filled, _, _ = cv2.floodFill(filled, None, seed_point, 128)
        
        # Fill in remaining spots with pxl value = 0 (inside the boundaries) and change to 255
        filled = np.where(filled == 0, 255, 0).astype(np.uint8) 
        filled[boundary_mask] = 255
    
    else:
        print("No background seed point found. Check image for boundary coverage.")

    return filled

# 2. Fill and write new tiff ########################################################
def fill_and_write_tiff(edge_tiff_path, output_dir):
    
    '''
    Fill in iceberg outlines and create a filled GeoTIFF image. 
    '''
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    img_id = edge_tiff_path.split('/')[-1]
    output_file = 'filled_' + img_id
    output_path = os.path.join(output_dir, output_file)
    
    with rasterio.open(edge_tiff_path) as src:
        
        # Load in binary iceberg GeoTIFF...
        image = src.read(1)
        
        # Gather metadata from original tiff file to add to filled tiff 
        transform = src.transform
        crs = src.crs
        profile = src.profile
        profile.update(nodata=None)  
        profile.update(dtype='uint8')
        
        # Fill in icebergs
        flood_filled_image = flood_fill_with_boundaries(image)  
        
        # Write filled image to a new tiff file
        with rasterio.open(output_path, 'w', **profile) as dst:
            dst.write(flood_filled_image.astype(np.uint8), 1)  

# MAIN ####################################################################################
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Fill in binary geotiffs of iceberg outlines')
    parser.add_argument('-e', '--edges', required = True, help = 'Path to source directory binary iceberg outline tiffs')
    parser.add_argument('-d', '--dest', required = True, help = 'Path to destination directory for the filled-in tiffs')
    args = parser.parse_args()
    
    edge_tifs = glob(os.path.join(args.edges, '*.tif'))

    for edge_tif in tqdm(edge_tifs):
        fill_and_write_tiff(edge_tiff_path=edge_tif, output_dir=args.dest)