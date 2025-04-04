# Calculating Ice Proportions within the Johns Hopkins Inlet

## Overview
This repository contains a pipeline for calculating the proportion of glacial ice in aerial images from the Johns Hopkins Inlet in Glacier Bay National Park. The workflow combines image processing, spatial analysis, and georeferencing to estimate ice coverage within defined spatial grid cells. It is designed to support environmental monitoring research on the harbor seal (*Phoca vitulina*).

## Features
- Converts `.jpg` aerial images and associated `.jgw` world files into georeferenced binary rasters
- Transforms rasters between coordinate reference systems (e.g., EPSG:3338 → EPSG:4326)
- Applies image processing techniques to fill in iceberg boundaries
- Calculates the proportion of ice per grid cell 
- Uses Lattice Kriging to estimate ice proportions at unobserved locations
- Outputs georeferenced raster layers for downstream analysis and mapping

## Installation

This pipeline uses both Python and R. Recommended setup:

1. Clone the repository:
   ```bash
   git clone https://github.com/nick-calzada/seal_ice.git
   cd seal_ice
   ```

2. Set up a Python environment (e.g., with `conda`):
   ```bash
   conda create -n ice_env python=3.11
   conda activate ice_env
   pip install -r requirements.txt
   ```

3. Install R dependencies:
   Ensure you have R installed and the following packages:
   - `sf`
   - `raster`
   - `stars`
   - `tidyverse`
   - `LatticeKrig`
   - `glue`
   - `here`

## Directory Structure
```txt
seal_ice/
├── data/
│   └── survey_date/
│       ├── created_data/
│       │   ├── edge_pngs_n_pgws/          # PNG edge images and associated PGW world files
│       │   ├── filled_tiffs/              # Flood-filled TIFFs of full iceberg areas
│       │   ├── wgs84_tiffs_from_pngs/     # CRS-transformed TIFFs (e.g., EPSG:4326)
│       │   └── valid_footprints.txt       # List of valid footprints used for analysis
│       └── original_data/
│           ├── edge_jpgs_n_jgws/          # Original JPG edge images and JGW world files
│           ├── jgws/                      # Raw .jgw files
│           └── npzs/                      # Numpy .npz iceberg data arrays
│
├── scripts/
│   ├── step_0_1_find_valid_fps_and_get_fp_ints.R
│   ├── step_2_npz_to_png.py
│   ├── step_2_3.py                        # Combines steps 2 and 3
│   ├── step_3_make_edge_pgw.py
│   ├── step_4_convert_crs.py
│   ├── step_5_fill_tiffs.py
│   ├── step_5_6.py                        # Combines fill + ice proportion calculation
│   ├── step_6_calc_ice_props.py
│   └── step_7_8_skeletons_to_lattice_krig.R
│
├── grid_cells_20070618_SB/                # Grid cells based on June 18, 2007 survey boundary
│   ├── {survey_date}_grid_cells.shp
│   ├── {survey_date}_grid_cells.dbf
│   ├── {survey_date}_grid_cells.prj
│   └── {survey_date}_grid_cells.shx
│
├── lk_rasters/
│   └── LK_ice_estimates_{survey_date}.tiff
│
├── requirements.txt
└── README.md
```

## Usage

Recommended order of operations:

1. **Find valid footprints and their intersections with the bathymetry raster.**  
   This step identifies usable image footprints and corresponding grid cell geometries (can be run first while performing steps 2-3 as it may take a while to run).

2. **Convert `.npz` iceberg arrays to `.png` images and create `.pgw` world files.**  
   Use `step_2_3.py`.

3. **Reproject the images using QGIS.**  
   (Or use `step_4_convert_crs.py` if you're scripting this.)

4. **Fill iceberg outlines and calculate ice proportions.**  
   Use `step_5_6.py` to generate filled rasters and grid-level proportion data.

5. **Create interpolated raster estimates using Lattice Kriging.**  
   Run `step_7_8_skeletons_to_lattice_krig.R`.

Each step saves intermediate outputs that can be reused for validation or inspection.

## Input Requirements
- Aerial `.jpg` images
- Corresponding `.jgw` world files with correct CRS
- Grid cell shapefiles
- Optional date-specific survey boundary shapefile

## Output
- Binary `.tif` images with 0 (non-ice) and 255 (ice) values
- Raster layers of ice proportions per grid cell
- `.csv` summaries of ice coverage by image, date, and grid cell

## Notes
- The pipeline assumes `.jgw` world files use **negative pixel width** and **positive pixel height**.
- Use of visualizations can assist in validating outputs

