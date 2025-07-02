from .manim_vector_field import VectorFieldAnimation
from .era5_processor import ERA5DataProcessor
from typing import List
import xarray as xr

def wrapper_vector_field_animation(API_KEY: str,
                                   roi: List,
                                   time: str,
                                   date: str,
                                   include_features:bool=False,
                                   colorized_animation:bool=False,
                                   title: str = 'ERA5 Wind Animation',
                                   colorscheme = 'viridis') -> VectorFieldAnimation:
    """
    Wrapper function to create Wind animation 

    """
    
    ### Create an instance of ERA5Processor
 
    
    ## Checking Connection
    print('Checking Connection with Destination Earth')
    try:
        ds = xr.open_dataset(
        f"https://edh:{API_KEY}@data.earthdatahub.destine.eu/era5/reanalysis-era5-single-levels-v0.zarr",
        chunks={},
        engine="zarr",
        )  
    except Exception as e:
        print(f"Error connecting to ERA5 dataset: {e}")
        return None
    
    ## 
    print('Retrieving data from ERA5...')
    
    processor = ERA5DataProcessor(
        ds=ds,
        variables=['u10', 'v10', 't2m'],
        date_range=[date, date],
        spatial_range={
            'lat': [float(roi[1]),float(roi[3])],
            'lon': [float(roi[0]),float(roi[2])]
        }
    )
    
    processor.process_data()
     

    print('Pre-Processing Data...')
    # Calculate wind speed
    processor.calculate_wind_speed()
                                                                    
    # Return the processed dataset
    dataset = processor.get_processed_data()

    # Create a subsampling dataset
    dataset_subsampled = processor.subsample_data(2)

    # Extract variables by a given timestep e.x: 10:00am
    extract_var = ['u10', 'v10', 't2m','wind_speed']
    dict_extract_var = processor.extract_components_by_given_timestep(extract_variables = extract_var,
                                                                    timestep=int(time[:2]), ##10:00am
                                                                    lat_long=True)
    
    print('Pre-processing complete. Creating animation...')
    ## selected the time 
    dataset_subsampled_10am = dataset_subsampled.isel(valid_time=int(time[:2])) ## 10:00 am

    ## Create the Animator instance
    vf = VectorFieldAnimation()

    
    # Set the wind dataset in the class
    vf.set_dataset(dataset_subsampled_10am)
    
    # Create the background image and set under the hood
    vf.create_background_image(
        dict_extract_var=dict_extract_var,
        var_heatmap = 'wind_speed' 
    )
    
    if include_features is False:  
        ## Returns the scene class
        Animation = vf.get_scene_class()
        
        return Animation
    
    else: 
        ## Config title
        vf.configure_title(
            show_title = True,
            title = title,
            font_size= 36
        )

        ## Config suptitle
        vf.configure_subtitle(
            show_subtitle = True,
            font_size=16,
            subtitle = f"{date} - {time} UTC"
        )

        if colorized_animation is True:
            ## Config colorbar
            vf.configure_colorbar(
                show=True,
                palette = colorscheme, ## Palette - from matplotlib palettes
                num_colors = 4 ,
                figsize = (1.0,9)
            )
        Animation = vf.get_scene_class()
        return Animation

        
        