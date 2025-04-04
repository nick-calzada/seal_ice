setwd('~/seal')
library(here)
library(LatticeKrig)
library(tidyverse)
library(glue)
library(raster)
library(sf)
################################################################################
# Using observed ice proportions and LatticeKrig(), create a smooth ice proportion
# map across the JHI domain for a specific replicate date
################################################################################

# 03/04 - most recent attempt is with covariates (glacier distance which depends on survey date, and bathymetry)

# Since we now only want to use one survey bonday (20070618), perform all of those
# steps before the loop, as doing so inside is redundant 

# Read in survey polygon for specified replicate date
path <- here("harbor_seal_many_replicates", "survey_polygons")
layer <- glue('JHI_20070618_surveyboundary')
survey.poly <- st_read(dsn = path, layer = layer)

# Convert CRS to WGS84 (EPSG:4326)
survey.poly <- st_transform(survey.poly$geometry, crs = 4326)
survey.poly.mat <- survey.poly[[1]][[1]]

# Read in bathymetry raster for proper grid cell geometries
print('Constructing empty dataframe with cell coordinates...')
bath.rast <- raster(here("covs", "bathymetry.tiff"))
bath.rast.survey <- raster::crop(bath.rast, extent(survey.poly.mat))
bath.rast.survey <- raster::mask(bath.rast.survey, as(survey.poly, 'Spatial'))
bath.survey.idx <- which(!is.na(values(bath.rast.survey))) # indices of values != NA
full.coord <- xyFromCell(bath.rast.survey, bath.survey.idx) # centers of these cells (idx numbers)
empty <- data.frame(full.coord)

# Gather command line arguments and check for validity
args <- commandArgs(trailingOnly = TRUE)
if (length(args) == 0) {
  stop(
    "Usage: Rscript get_fp_ints_any_rep_date.R <rep_date_1> <rep_date_2> <...rep_date_N>"
  )
}
replicates <- as.numeric(args)
if (any(is.na(replicates))) {
  stop("Error: All arguments must be numeric, non-empty values (replicate date(s)).")
}

for (replicate_date in replicates) {
  
  ###########################################################################
  # 1. Make the ice prop skeleton
  ###########################################################################
  
  # If using each survey date's unique survey boundaru, use the commented code below
  # Read in footprint shapes 
  # path <- here("harbor_seal_many_replicates", "footprints")
  # layer <- glue('JHI_{replicate_date}_footprint')
  # footprint <- st_read(dsn = path, layer = layer)
  
  # # Read in survey polygon for specified replicate date
  # path <- here("harbor_seal_many_replicates", "survey_polygons")
  # layer <- glue('JHI_{s}_surveyboundary')
  # survey.poly <- st_read(dsn = path, layer = layer)
  # 
  # # Convert CRS to WGS84 (EPSG:4326)
  # survey.poly <- st_transform(survey.poly$geometry, crs = 4326)
  # survey.poly.mat <- survey.poly[[1]][[1]]
  # 
  # # Read in bathymetry raster for proper grid cell geometries
  # bath.rast <- raster(here("covs", "bathymetry.tiff"))
  # bath.rast.survey <- raster::crop(bath.rast, extent(survey.poly.mat))
  # bath.rast.survey <- raster::mask(bath.rast.survey, as(survey.poly, 'Spatial'))
  # bath.survey.idx <- which(!is.na(values(bath.rast.survey))) # indices of values != NA
  # full.coord <- xyFromCell(bath.rast.survey, bath.survey.idx) # centers of these cells (idx numbers)
  # empty <- data.frame(full.coord)
  
  # Load in ice proportion data 
  # file_name <- glue('good_ice_props/{s}_ice_props.csv')
  file_name <- glue('final_ice_props_w_one_sb/ice_props_{replicate_date}.csv')
  ice <- read_csv(file_name) %>% dplyr::select(-...1, -geometry) %>% as.data.frame()
  
  # Some EDA
  # any(is.na(ice$z)) # no NA observed z values
  # print(paste('min:', min(ice$z), 'max:', max(ice$z)))
  # hist(ice$z)
  # summary(ice$z)
  
  # Normalize ice-prop values to be between 0 and 1 using min-max normalization; some values slightly above 1 due to floating point division in previous step.
  min_z <- min(na.omit(ice$z))
  max_z <- max(na.omit(ice$z))
  min_maxed_ice <- ice %>% mutate(min_max_z = (z - min_z) / (max_z - min_z))
  min_maxed_ice <- min_maxed_ice %>% dplyr::select(-z, z = min_max_z)
  print(paste('normalized min:', min(min_maxed_ice$z), 'normalized max:', max(min_maxed_ice$z)))
  
  # Join empty and ice proportion data frames
  precision <- 12 # Define the desired precision
  
  # Round the coordinates in both datasets
  empty <- empty %>% mutate(x = round(x, precision), y = round(y, precision))
  min_maxed_ice <- min_maxed_ice %>% mutate(x = round(x, precision), y = round(y, precision))
  
  # Perform the join and anti-join
  df <- left_join(empty, min_maxed_ice, by = c("x", "y")) %>% dplyr::select(x, y, z) 
  anti <- anti_join(min_maxed_ice, empty, by = c('x', 'y')) # should be an empty dataframe
  
  # Visualize observed ice proportions.
  # ggplot() + 
  #   geom_tile(data = df, aes(x=x,y=y,fill=z)) + 
  #   coord_sf() +
  #   scale_fill_viridis()
  
  # Optional to save or not, depnding on how pipeline is performed. Here it does not need to be saved since it is used in step 2 immediately after.
  # file_name <- glue('new_ice_prop_skeletons/ice_props_{replicate_date}.csv')
  # write_csv(df, file = file_name)
  
  ###########################################################################
  # 2. Perform LatticeKrig() interpolation
  ###########################################################################
  
  # replicate_date <- 20070621
  # glac.dist.name <- glue('covs/glacier_dist_{replicate_date}.tiff')
  # glac.dist.rast <- raster(glac.dist.name)
  # glac.dist.rast <- raster('covs/glacier_dist_20070619.tiff')
  
  print(glue('Beginning {replicate_date} survey ...'))
  # file_name <- glue('ice_prop_skeletons/ice_props_{replicate_date}.csv')
  # file_name <- 'final_ice_props_w_one_sb/march_10_20070618_test.csv'
  # df <- read_csv(file_name, show_col_types = FALSE) %>% as.data.frame()
  
  # Construct design matrix
  print('Constructing design matrix ...')
  
  X.full <- data.frame(x = df[, 'x'],
                       y = df[, 'y'], 
                       z = df[, 'z']
                       # glac_dist = scale(raster::extract(x = glac.dist.rast, y = df[,c('x', 'y')])),
                       # bath = scale(raster::extract(x = bath.rast, df[,c('x', 'y')]))
                       )
  
  # Gather observed proportions and locations
  X.obs <- X.full %>% filter(!is.na(z))
  X.unobs <- X.full %>% filter(is.na(z))
  locations <- X.obs[, c('x', 'y')]
  observations <- X.obs[, 'z']
  
  # Fit LK model with no covariates
  print('Fitting LatticeKrig model ...')
  iceFit <- LatticeKrig(locations, observations) # Unspecified, "black box" version
  
  # Predict at unobserved locations
  print('Predicting ice proportions at unobserved locations ...')
  # cov.mat <- X.unobs[, c('glac_dist', 'bath')] %>% as.matrix()
  gHat <- predict(iceFit, X.unobs[, c('x', 'y')]) # w covs
  
  # Join fitted values at observed locations with predicted values
  print('Joining fitted values and estimated values ...')
  fitted_vals <- cbind(X.obs[, c('x', 'y')], z = iceFit$fitted.values)
  preds <- cbind(X.unobs[, c('x', 'y')], z = gHat)
  joined <- rbind(fitted_vals, preds)
  
  # Clip any estimates that fall outside of [0,1]
  joined <- joined %>%
    mutate(clipped_z = pmin(pmax(z, 0), 1))
  
  print(range(joined$clipped_z))
  
  # Optional: visualize final ice proportion map
  # p <-
  #   ggplot() +
  #   geom_tile(data = joined, aes(x = x, y = y, fill = clipped_z)) +
  #   scale_fill_viridis() +
  #   coord_sf() +
  #   theme_bw() +
  #   labs(title = 'LatticeKrig fitted values at data locations and estimated values at unobserved locations (no covs)')
  # p
  
  # Clean final data frame and convert to raster (.tiff)
  final <- joined %>% dplyr::select(x, y, z = clipped_z)
  r <- raster::rasterFromXYZ(final, crs = 4326)
  raster_name <- glue('lk_rasters/20070618_sb/LK_ice_estimates_{replicate_date}.tiff')
  print(glue('Writing {raster_name}'))
  raster::writeRaster(r, raster_name, overwrite=TRUE)
}
