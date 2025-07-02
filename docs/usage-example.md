# Usage Example

In order to exemplify the data processor, each module is exemplified below:

## ERA5 Processor


```python
import xarray as xr
from era5_processor import ERA5DataProcessor

# Load ERA5 dataset
era5_data = xr.open_dataset('era5_data.nc')

# Initialize processor
processor = ERA5DataProcessor(
    ds=era5_data,
    variables=['u10', 'v10', 'msl'],  # 10m winds and mean sea level pressure
    date_range=['2023-06-01', '2023-06-30'],
    spatial_range={
        'lat': [40, 60],    # Northern Europe
        'lon': [-10, 30]    # Atlantic to Eastern Europe
    },
    convert_longitude=True,
    include_attributes=True
)

# Process the data
processor.process_data()

# Calculate wind speed
processor.calculate_wind_speed()

# Get processed dataset
full_data = processor.get_processed_data()

# Extract specific timestep for plotting
plot_data = processor.extract_components_by_given_timestep(
    timestep=0,
    extract_variables=['u10', 'v10', 'wind_speed'],
    lat_long=True
)

# Create subsampled dataset for streamlines
streamline_data = processor.subsample_data(step=3)
```

## Colorbar

#### Basic Matplotlib Palette
```python
from colormap import ColorPalette

# Create palette for wind speed visualization
wind_palette = ColorPalette(
    palette='viridis',
    num_colors=50,
    data_min=0,
    data_max=25  # m/s
)

# Get discrete colors
colors = wind_palette.get_hex_colors()

# Map specific values
calm_color = wind_palette.get_color_for_value(2)      # Light wind
strong_color = wind_palette.get_color_for_value(20)   # Strong wind
```

#### Custom Hex Color Palette
```python
# Define custom color scheme
custom_colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D']

temp_palette = ColorPalette(
    palette=custom_colors,
    num_colors=20,
    data_min=-10,
    data_max=40  # Temperature range in °C
)

# Extract interpolated colors
temp_colors = temp_palette.get_hex_colors()
```

#### Advanced Visualization
```python
# Create and customize colorbar
pressure_palette = ColorPalette(
    palette='RdYlBu_r',
    num_colors=100,
    data_min=990,
    data_max=1030  # hPa pressure range
)

# Save publication-ready colorbar
pressure_palette.save_plot(
    filename='pressure_colorbar.pdf',
    dpi=300,
    title='Sea Level Pressure (hPa)',
    title_size=14,
    label_size=12,
    figsize=(2, 8),
    width_ratio=0.7
)
```

#### Integration with Data Visualization
```python
# Use with matplotlib plotting
import matplotlib.pyplot as plt
import numpy as np

# Create sample data
data = np.random.uniform(0, 50, (100, 100))

# Create palette
palette = ColorPalette('plasma', num_colors=256, data_min=0, data_max=50)

# Create plot with custom colormap
fig, ax = plt.subplots()
im = ax.imshow(data, cmap=palette._colormap, vmin=0, vmax=50)

# Add colorbar
cbar = plt.colorbar(im, ax=ax)
cbar.set_label('Wind Speed (m/s)')
```

## Base Plot

```python
import cartopy.crs as ccrs
import numpy as np

# Basic usage with heatmap only
data = {
    'long': np.linspace(-10, 10, 100),
    'lat': np.linspace(40, 60, 100), 
    'wind_speed': np.random.rand(100, 100)
}

filename = create_layer_base(
    dict_extract_var=data,
    var_heatmap='wind_speed',
    file_name='wind_heatmap.png',
    cmap='viridis',
    dpi=150
)

# Usage with streamlines
import xarray as xr

# Assuming you have a subsampled dataset for streamlines
streamline_data = xr.Dataset({
    'u10': (['latitude', 'longitude'], u_component_data),
    'v10': (['latitude', 'longitude'], v_component_data),
    'longitude': longitude_coords,
    'latitude': latitude_coords
})

filename = create_layer_base(
    dict_extract_var=data,
    var_heatmap='wind_speed',
    file_name='wind_with_streams.png',
    stream_lines=True,
    dataset_subsampled=streamline_data,
    density=15,  # streamplot parameter
    linewidth=0.6  # streamplot parameter
)

# Using different coordinate reference system
filename = create_layer_base(
    dict_extract_var=data,
    crs_transform=ccrs.Mercator(),
    file_name='mercator_projection.png'
)
```


## VectorField Animation

### Basic Usage

```python
import xarray as xr
from your_library import VectorField_Animation

# Load your ERA5 dataset
dataset = xr.open_dataset('era5_wind_data.nc')

# Initialize the animator
animator = VectorField_Animation(
    dataset=dataset,
    background_image_path='map_background.png'
)

# Configure the animation
animator.configure(
    output_file='my_wind_animation',
    quality='high_quality'
).configure_title(
    show_title=True,
    title_text='Wind Flow Analysis'
).configure_streamplot(
    flow_speed=3.0,
    color='BLUE'
)

# Render in notebook
animator.render_to_notebook()
```

### Advanced Configuration

```python
# Complex configuration with all options
animator = VectorField_Animation() \
    .set_dataset(dataset) \
    .set_background_image('detailed_map.png') \
    .configure(
        output_file='detailed_wind_analysis',
        pixel_width=1920,
        pixel_height=1080,
        quality='fourk_quality'
    ) \
    .configure_baseplot(
        image_height=6.5
    ) \
    .configure_title(
        show_title=True,
        title_text='High Resolution Wind Analysis',
        title_font_size=48,
        title_color='YELLOW'
    ) \
    .configure_suptitle(
        show_suptitle=True,
        suptitle_font_size=28
    ) \
    .configure_streamplot(
        delta_y=0.1,
        resize_factor=0.02,
        stroke_width=1.5,
        flow_speed=4.0,
        time_width=0.4,
        animation_duration=5,
        max_anchors_per_line=150,
        color='CYAN',
        virtual_time=6
    )

# Generate preview first
animator.preview()

# Then render full animation
animator.render_to_notebook(display_mode='video')
```

### Configuration Inspection

```python
# Get all configurations
all_configs = animator.get_config()

# Get specific section
streamplot_config = animator.get_config('streamplot')
print(f"Current flow speed: {streamplot_config['flow_speed']}")

# Modify and reapply
streamplot_config['flow_speed'] = 5.0
animator.configure_streamplot(**streamplot_config)
```

## Chaining Methods

All configuration methods return `self`, enabling convenient method chaining for setup:

```python
animator.configure(quality='high_quality') \
        .configure_title(show_title=True) \
        .configure_streamplot(flow_speed=3.0) \
        .render_to_notebook()
```


## teste

## Usage Examples

### Basic Usage
```python
# Create and configure animation
animation = VectorFieldAnimation()
animation.set_dataset(wind_dataset) \
         .set_background_image("map.png") \
         .configure_title(show_title=True, title_text="Wind Patterns") \
         .configure_streamplot(flow_speed=3.0, animation_duration=5.0)

# Check if ready and get scene class
if animation.is_ready():
    scene_class = animation.get_scene_class()
else:
    print("Missing:", animation.get_missing_requirements())
```

### Advanced Configuration
```python
animation = VectorFieldAnimation()

# Set up data and background
animation.set_dataset(wind_data) \
         .create_background_image(
             extracted_data,
             var_heatmap='wind_speed',
             cmap='viridis',
             dpi=300,
             stream_lines=True,
             dataset_subsampled=subsampled_data
         )

# Configure appearance
animation.configure_title(
    show_title=True,
    title_text="Global Wind Patterns",
    font_size=48,
    title_color="BLUE"
).configure_subtitle(
    show_suptitle=True,
    suptitle_text="January 2024",
    font_size=24
).configure_streamplot(
    delta_y=0.1,
    flow_speed=2.5,
    stroke_width=1.5,
    color="YELLOW",
    animation_duration=10.0
).configure_colorbar(
    palette='plasma',
    num_colors=10,
    data_min=0,
    data_max=25
)

# Preview configuration
config_summary = animation.preview_config()
print(config_summary)

# Generate scene
scene_class = animation.get_scene_class()
```