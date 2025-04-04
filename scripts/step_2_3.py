import argparse
from step_2_npz_to_png import npz_to_png
from step_3_make_edge_pgw import make_edge_pgw
import os

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Input survey date')
    parser.add_argument('--date', '-d', nargs = '+', required=True, help = 'Date(s) of surveys (e.g., 20070618, 20070619, ...)')
    # parser.add_argument('--date', '-d', required=True, help = 'Month and day of survey date (MMYY).')

    args = parser.parse_args()
    dates = args.date
    print(f'\nDates provided: {dates}')

    for d in dates:

        # make directory/filenames based on the survey date input by the user 
        source_dir = os.path.join('data', d, 'original_data', 'npzs')
        print(f'\nCreating PNG images from {source_dir}')
        dest_dir = os.path.join('data', d, 'created_data', 'edge_pngs_n_pgws')
        print(f'Writing PNGs to {dest_dir}')


        # 1. Convert npz files to binary png files
        npz_to_png(source_dir=source_dir, dest_dir=dest_dir)

        # 2. Create a corresponding pgw file
        jgw_source = os.path.join('data', d, 'original_data', 'jgws')
        print(f'\nWriting pgw files to {dest_dir}')
        make_edge_pgw(source_dir=jgw_source, dest_dir=dest_dir)

