import os
import numpy as np
from glob import glob 
from tqdm import tqdm
import argparse

def make_edge_pgw(source_dir, dest_dir):
    
    '''
    Use the original .jgw world files to create corresponding .pgw files for the newly created PNG images.

    What's a world file?
    A world file provides georeferencing information for a corresponding image. It defines how to convert between image pixel coordinates and real-world spatial coordinates.

    Each world file contains six lines with the following information:

    1. Pixel size in the x-direction (width of a pixel in map units)
    2. Rotation about the y-axis (typically 0 for north-up images)
    3. Rotation about the x-axis (typically 0 for north-up images)
    4. Pixel size in the y-direction (height of a pixel in map units; usually negative to indicate that the origin is at the top-left)
    5. X-coordinate of the center of the upper-left pixel
    6. Y-coordinate of the center of the upper-left pixel
    '''
    
    if not os.path.exists(source_dir):
        raise FileNotFoundError(f"Source directory '{source_dir}' does not exist.")

    jgw_paths = glob(os.path.join(source_dir, '*.jgw'))

    for source_file in tqdm(jgw_paths[:]):
        img_id = source_file.split('/')[-1].split('.')[0]
        jgw_name = img_id + '_iceberg_edges.pgw'
        final_dest = os.path.join(dest_dir, jgw_name)
        
        with open(source_file, 'r') as src, open(final_dest, 'w') as dest:
            dest.write(src.read())

    print('Successfully created PGW files for iceberg PNG images!')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Make PGW files for PNG images using information in JGW files')
    parser.add_argument('--source', required=True, help = 'Path to source directory with original JPG and JGW files')
    parser.add_argument('--dest', required = True, help = 'Path to destination directory with PNG images')
    args = parser.parse_args()
    make_edge_pgw(source_dir=args.source, dest_dir=args.dest)
    