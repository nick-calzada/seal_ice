import os
import numpy as np
from glob import glob 
from PIL import Image
from tqdm import tqdm
import argparse

def npz_to_png(source_dir, dest_dir):
    
    '''
    Convert binary .npz files to .png images. 
    '''

    if not os.path.exists(source_dir):
        raise FileNotFoundError(f"Source directory '{source_dir}' does not exist.")

    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    npz_paths = glob(os.path.join(source_dir, '*.npz'))
    
    if not npz_paths:
        print(f"No .npz files found in the source directory '{source_dir}'.")
        return

    for n in tqdm(npz_paths):
        
        img_id = n.split('/')[-1].split('.')[0]
        img_id = img_id.replace('icebergs', 'iceberg_edges')
        png_name = img_id + '.png'
        final_dest = os.path.join(dest_dir, png_name)
        edges = np.load(n)['edges']
        
        if edges.shape != (2138, 3218):
            print(f"Skipping file {img_id}: shape {edges.shape} does not match (2138, 3218)")
            continue

        # Save image as a PNG to avoid lossy compression
        img = Image.fromarray(edges)
        img.save(final_dest, format = 'PNG')
        
    print('Successfully converted edge arrays to png images!')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert .npz files to PNG images')
    parser.add_argument('--source', required = True, help = 'Path to source directory containing .npz files')
    parser.add_argument('--dest', required = True, help = 'Path to destination directory for the PNG images')
    args = parser.parse_args()
    npz_to_png(source_dir=args.source, dest_dir=args.dest)
    