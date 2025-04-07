
################################################################################
# Step 0: Find valid (nonempty) footprints.
# Step 1: Gather coordinates and shapes of grid cells for finding ice proportions
# later in the pipeline. 
# Recommend to run this first in the background for replicate date(s) of interest.
################################################################################

library(sf)
library(here)
library(tidyverse)
library(spatstat)
library(stars)
library(raster)
library(glue)

# Gather command line arguments (replicate date(s)) and check for validity
args <- commandArgs(trailingOnly = TRUE)
if (length(args) == 0) {
  stop(
    "Usage: Rscript get_fp_ints_any_rep_date.R <rep_date_1> <rep_date_2> <...rep_date_N>"
  )
}
surveys <- as.numeric(args)
if (any(is.na(surveys))) {
  stop("Error: All arguments must be numeric, non-empty values (replicate date(s)).")
}

# Function to find npz files for which there are valid binary npz files for
find_valid_footprints <- function(rep_year) {
  npz_files <- here('data', rep_year, 'raw', 'npzs')
  txt_file_name <- here('data', rep_year, 'created', 'valid_footprints.txt')
  fileConn <- file(txt_file_name, "w")
  writeLines("files", fileConn)
  files <- list.files(npz_files)
  for (f in files) {
    name <- sub("\\.npz$", "", f)  # Remove the .npz extension
    name <- gsub("_icebergs", "", name)  # Remove '_icebergs'
    name <- paste0(name, ".JPG")  # Add .JPG extension
    writeLines(name, fileConn)
  }
  close(fileConn)
}

# Iterate through user-specified survey date(s)
for (s in surveys) {
  
  # Find valid footprints 
  print('Gathering valid footprints ...')
  find_valid_footprints(s)
  
  # Read in footprint shapes
  path <- here("harbor_seal_many_replicates", "footprints")
  layer <- glue('JHI_{s}_footprint')
  footprint <- st_read(dsn = path, layer = layer)
  
  # Read in survey polygon for specified replicate date
  path <- here("harbor_seal_many_replicates", "survey_polygons")
  
  # Previously had been altering by specific survey boundary date but lets just use one...
  # layer <- glue('JHI_{s}_surveyboundary')
  layer <- 'JHI_20070618_surveyboundary'
  survey.poly <- st_read(dsn = path, layer = layer)
  
  # Convert CRS to WGS84 (EPSG:4326)
  survey.poly <- st_transform(survey.poly$geometry, crs = 4326)
  survey.poly.mat <- survey.poly[[1]][[1]]
  
  # Filter for valid footprints
  print('Filtering for valid footprints ...')
  # path <- here(glue('data/{s}/created_data/valid_footprints.txt'))
  path <- here('data', as.character(s), 'created', 'valid_footprints.txt')
  desired_files <- read_csv(path, show_col_types = FALSE)
  filtered.footprint <- footprint %>% filter(FileName %in% desired_files$files)
  footprint <- filtered.footprint
  footprint$geometry <- st_transform(filtered.footprint$geometry, crs = 4326)
  
  # Read in bathymetry raster for proper grid cell geometries
  bath.rast <- raster(here("covs", "bathymetry.tiff"))
  
  # Crop bath data using survey boundary
  bath.rast.survey <- raster::crop(bath.rast, extent(survey.poly.mat))
  bath.rast.survey <- raster::mask(bath.rast.survey, as(survey.poly, 'Spatial'))
  
  # Convert raster to sf object
  bath_stars <- st_as_stars(bath.rast.survey)
  
  # Set merge to false!!!! Do not want cells with the same value to be merged into a single cell!
  bath_sf <- st_as_sf(bath_stars, as_points = FALSE, merge = FALSE)
  
  # Get grid centers
  bath.survey.idx <- which(!is.na(values(bath.rast.survey))) # indices of values != NA
  full.coord <- xyFromCell(bath.rast.survey, bath.survey.idx) # centers of these cells (idx numbers)
  
  results <- c()
  
  # Iterate over each footprint
  for (f in 1:nrow(footprint)) {
    # Extract footprint geometry and file name
    fp_poly <- footprint[f, ]$geometry
    file_name <- footprint[f, ]$FileName
    
    # Perform the intersection
    print(paste0('Intersecting ', file_name, ' with bathymetry raster...'))
    footprint_bath_int <- st_intersection(bath_sf, fp_poly)
    
    # Extract the intersected cell IDs
    cell_ids <- as.numeric(rownames(footprint_bath_int))  # Ensure your raster cells have an ID
    
    # full_coord_rownames <- as.numeric(rownames(as.data.frame(full.coord)))
    if (length(cell_ids) == 0) {
      print(glue(
        'Skipping iteration for {file_name}; outside of survey area.'
      ))
      next
    }
    
    # Extract the corresponding cell center coordinates
    cell_centers <- full.coord[cell_ids, , drop = FALSE]  # Subset using cell IDs
    
    # Combine the results into a data frame
    df <- data.frame(
      file_name = basename(file_name),
      cell_geometry = footprint_bath_int$geometry,
      cell_center_coord = (cell_centers)
    )
    
    # Filter for intact cells
    df <- st_as_sf(df)
    df$area <- as.numeric(st_area(df))
    min_area <- max(df$area) - 0.1
    filtered_areas <- df %>% filter(area >= min_area)
    
    # Append to results list
    results[[f]] <- filtered_areas
  }
  
  df <- do.call(rbind, results) %>% st_as_sf()
  
  # Extract the x and y coordinates and convert geo column to sf polygon object
  final_df <- df %>% rename(x = cell_center_coord.x, y = cell_center_coord.y) %>%
    st_as_sf(sf_column_name = 'geometry')
  
  # Save output shape file
  output_dir <- 'grid_cells_20070618_SB'
  output_path <- here(output_dir, glue("{s}_grid_cells.shp"))
  st_write(final_df, output_path, append = FALSE)
}
