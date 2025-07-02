# API Documentation

Lombricquiver is an aggregation of the following modules:

* [`ERA5_Processor`](#era5-processor) - Retrieve and Pre-process geospatial data from ERA5.
* [`Colormap`](#colormap) - Allow palette generation .
* [`VectorFieldAnimation`](#vectorfieldanimation) - Creates the Scene and animate stream lines.
* [`Base plot`](#base-plot) - Deals with background plots that belongs to the scene.

## **ERA5 Processor**

The ERA5_Processor module provides functionality for retrieving and pre-processing geospatial data from ERA5 datasets. It handles data filtering, coordinate transformations, variable extraction, and wind calculations.

### Classes


#### `ERA5DataProcessor`

```python
ERA5DataProcessor(
    ds,
    variables,
    date_range,
    spatial_range,
    convert_longitude=True,
    include_attributes=True
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ds` | `xr.Dataset` | *Required* | The source xarray dataset containing meteorological variables and coordinates |
| `variables` | `dict` or `list` | *Required* | Dictionary mapping source variable names to new names, or list of variable names to keep unchanged |
| `date_range` | `list` or `tuple` | *Required* | Date range for filtering: `[start_date, end_date]` in format `["YYYY-MM-DD", "YYYY-MM-DD"]` |
| `spatial_range` | `dict` | *Required* | Spatial boundaries with keys `'lat': [min_lat, max_lat]` and `'lon': [min_lon, max_lon]` |
| `convert_longitude` | `bool` | `True` | Whether to convert longitude from 0-360° to -180° to 180° |
| `include_attributes` | `bool` | `True` | Whether to copy variable attributes from the source dataset |

**Attributes:**

- `dataset`: Original dataset (copy of input)

- `loaded_dataset`: Processed dataset with data loaded into memory

- `variables`: Variable configuration

- `date_range`: Date filtering range

- `spatial_range`: Spatial filtering bounds

- `convert_longitude`: Longitude conversion setting

- `include_attributes`: Attribute copying setting

### Methods
 
 ---

#### `process_data()`


*Process Steps:*

1. Filter by date range using `valid_time` coordinate
2. Select specified variables
3. Convert longitude coordinates (if enabled)
4. Sort by longitude
5. Select spatial region of interest
6. Load data into memory

**Example:**
```python
processor = ERA5DataProcessor(
    ds=era5_dataset,
    variables=['u10', 'v10', 'msl'],
    date_range=['2023-01-01', '2023-01-31'],
    spatial_range={'lat': [35, 70], 'lon': [-15, 40]}
)
processor.process_data()
```
---

#### **`extract_components_by_given_timestep()`**

Extracts a specific timestep for selected variables and returns them as a dictionary.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `timestep` | `int` | *Required* | Time index to extract from the processed dataset |
| `extract_variables` | `list` or `dict` | *Required* | Variables to extract (list of names or dict mapping) |
| `lat_long` | `bool` | `True` | Whether to include latitude and longitude coordinates in output |

**Returns:**
- `Dict[str, xr.Dataset]`: Dictionary with variable names as keys and extracted data as values


**Example:**
```python
# Extract first timestep
timestep_data = processor.extract_components_by_given_timestep(
    timestep=0,
    extract_variables=['u10', 'v10', 'wind_speed'],
    lat_long=True
)
# Returns: {'u10': data, 'v10': data, 'wind_speed': data, 'lat': coords, 'long': coords}
```
--- 

#### **`calculate_wind_speed()`**

Calculates wind speed magnitude from u and v wind components and adds it to the processed dataset.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `u_component` | `str` | `'u10'` | Name of the east-west wind component variable |
| `v_component` | `str` | `'v10'` | Name of the north-south wind component variable |
| `new_var_name` | `str` | `'wind_speed'` | Name for the calculated wind speed variable |

**Calculation:**
Wind speed is calculated using: `sqrt(u² + v²)`

**Example:**
```python
# Calculate wind speed from 10m wind components
processor.calculate_wind_speed(
    u_component='u10',
    v_component='v10',
    new_var_name='wind_speed_10m'
)
```
---

#### **`subsample_data()`**

Creates a subsampled version of the processed dataset by taking every nth point.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `step` | `int` | `2` | Step size for subsampling (e.g., 2 takes every 2nd point) |

**Returns:**
- `xr.Dataset`: New subsampled dataset with reduced spatial resolution

**Example:**
```python
# Create dataset with half the spatial resolution
subsampled = processor.subsample_data(step=2)

# More aggressive subsampling
coarse_data = processor.subsample_data(step=4)
```
---

#### **`get_processed_data()`**

Returns the fully processed dataset. This is the last step of the processing chain and returns a xr.Dataset.

**Returns:**
- `xr.Dataset`: The processed dataset with all applied filters and calculations

**Example:**
```python
processed_dataset = processor.get_processed_data()
```

---
## Colormap

The Colormap module provides functionality for palette generation and color management. It handles matplotlib colormaps, custom hex color arrays, and provides utilities for color extraction and visualization.

### Classes

#### `ColorPalette`

A comprehensive class for handling matplotlib color palettes and custom hex color arrays. It provides methods for color extraction, value-to-color mapping, and palette visualization.

**Constructor:**
```python
ColorPalette(
    palette,
    num_colors=None,
    data_min=None,
    data_max=None
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `palette` | `str`, `matplotlib.colors.Colormap`, or `list` | *Required* | Color palette name (e.g., 'viridis', 'tab10'), colormap object, or list of hex color strings |
| `num_colors` | `int` | `None` | Number of colors to extract from the palette. Required for matplotlib palettes, defaults to list length for custom palettes |
| `data_min` | `float` | `0` | Minimum data value for color mapping |
| `data_max` | `float` | `num_colors` | Maximum data value for color mapping |

**Attributes:**

- `palette`: The input palette specification
- `num_colors`: Number of colors in the palette
- `data_min`: Minimum value for data range
- `data_max`: Maximum value for data range
- `is_custom`: Boolean indicating if palette is custom hex colors
- `_custom_colors`: List of custom hex colors (if applicable)
- `_colormap`: Internal matplotlib colormap object

### Methods

#### `get_hex_colors()`

Extracts hex color strings from the palette.

**Returns:**
- `list`: Array of hex color strings with length `num_colors`

**Behavior:**
- For custom palettes: Samples or interpolates from provided colors
- For matplotlib palettes: Samples evenly across the colormap range
- Handles cases where requested colors exceed available custom colors through interpolation

**Example:**
```python
# Matplotlib palette
palette = ColorPalette('viridis', num_colors=5)
colors = palette.get_hex_colors()
# Returns: ['#440154', '#31688e', '#35b779', '#fde725', ...]

# Custom hex colors
custom_palette = ColorPalette(['#FF5733', '#33FF57', '#5733FF'], num_colors=5)
colors = custom_palette.get_hex_colors()
# Returns: interpolated colors from the custom set
```

#### `get_color_for_value()`

Maps a specific data value to its corresponding hex color.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `value` | `float` | The data value to map to a color |

**Returns:**
- `str`: Hex color string corresponding to the normalized value

**Normalization:**
- Values are normalized to [0, 1] range using `(value - data_min) / (data_max - data_min)`
- Values outside the range are clamped to [0, 1]
- Handles edge case where `data_max == data_min`

**Example:**
```python
palette = ColorPalette('plasma', num_colors=100, data_min=0, data_max=50)

# Get color for specific wind speed
color_low = palette.get_color_for_value(5)    # Low wind speed
color_high = palette.get_color_for_value(45)  # High wind speed
color_mid = palette.get_color_for_value(25)   # Medium wind speed
```

#### `plot_palette()`

Creates a colorbar visualization of the palette with customizable appearance.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `figsize` | `tuple` | `(2, 8)` | Figure size as (width, height) in inches |
| `title` | `str` | `'m/s'` | Title/label for the colorbar |
| `title_size` | `int` | `12` | Font size for the title |
| `label_size` | `int` | `16` | Font size for tick labels |
| `width_ratio` | `float` | `0.8` | Width ratio of colorbar (larger = thinner bar) |

**Returns:**
- `matplotlib.figure.Figure`: The created figure object

**Features:**
- Vertical orientation colorbar
- Automatic normalization based on data range
- Customizable spacing and typography
- Extended colorbar with 'both' extend option

**Example:**
```python
# Basic colorbar
fig = palette.plot_palette(title='Wind Speed (m/s)')

# Customized appearance
fig = palette.plot_palette(
    figsize=(3, 10),
    title='Temperature (°C)',
    title_size=14,
    label_size=12,
    width_ratio=0.6  # Wider colorbar
)
plt.show()
```

#### `save_plot()`

Creates and saves a colorbar visualization to file.

**Signature:**
```python
save_plot(
    filename='colorbar',
    dpi=300,
    bbox_inches='tight',
    **kwargs
) -> None
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `filename` | `str` | `'colorbar'` | Output filename (extension determines format) |
| `dpi` | `int` | `300` | Resolution for output image |
| `bbox_inches` | `str` | `'tight'` | Bounding box specification |
| `**kwargs` | `dict` | `{}` | Additional arguments passed to `plot_palette()` |

**Supported Formats:**
- PNG, PDF, SVG, JPG, and other matplotlib-supported formats
- Format determined by file extension

**Example:**
```python
# Save with default settings
palette.save_plot('wind_colorbar.png')

# Save with custom settings
palette.save_plot(
    'temperature_scale.pdf',
    dpi=150,
    title='Temperature Scale',
    figsize=(2.5, 12),
    title_size=16
)
```

#### `__repr__()`

Provides string representation of the ColorPalette object.

**Returns:**
- `str`: Descriptive string showing palette configuration

---

## Base Plot 

The Base Plot module provides functionality for creating background plots and base layers for wind field data visualization.

### Functions

#### `create_layer_base`

Creates a base layer for plotting with heatmap visualization and optional streamlines. The function generates a PNG file with specified dimensions suitable for use as a background layer in animations.

**Signature:**
```python
create_layer_base(
    dict_extract_var,
    var_heatmap='wind_speed',
    dpi=300,
    height_inches=9,
    file_name='base_layer.png',
    crs_transform=ccrs.PlateCarree(),
    cmap='plasma_r',
    stream_lines=False,
    dataset_subsampled=None,
    **kwargs_streamplot
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `dict_extract_var` | `dict` | *Required* | Dictionary containing at least 'long', 'lat', and the variable to be plotted (e.g., 'wind_speed') |
| `var_heatmap` | `str` | `'wind_speed'` | The variable key from `dict_extract_var` to be used for the heatmap visualization |
| `dpi` | `int` | `300` | Dots per inch for the figure resolution |
| `height_inches` | `int` | `9` | Height of the figure in inches (designed to work with Manim canvas) |
| `file_name` | `str` | `'base_layer.png'` | Name of the output PNG file |
| `crs_transform` | `cartopy.crs.Projection` | `ccrs.PlateCarree()` | Coordinate reference system for the plot. Can be any valid Cartopy projection |
| `cmap` | `str` | `'plasma_r'` | Matplotlib colormap for the heatmap. See [Matplotlib colormap reference](https://matplotlib.org/stable/gallery/color/colormap_reference.html) |
| `stream_lines` | `bool` | `False` | Whether to include streamlines in the plot |
| `dataset_subsampled` | `xr.Dataset` | `None` | xarray dataset containing subsampled data for streamlines. Required when `stream_lines=True` |
| `**kwargs_streamplot` | `dict` | `{}` | Additional keyword arguments for the streamplot function (e.g., `density`, `linewidth`) |

**Required Dictionary Keys:**

The `dict_extract_var` parameter must contain:

- `'long'`: Longitude coordinates
- `'lat'`: Latitude coordinates  
- `var_heatmap`: The variable specified in the `var_heatmap` parameter (default: `'wind_speed'`)

**Streamline Dataset Requirements:**

When `stream_lines=True`, the `dataset_subsampled` parameter must be an xarray Dataset containing:

- `'longitude'`: Longitude coordinates
- `'latitude'`: Latitude coordinates
- `'u10'`: U-component of wind at 10m
- `'v10'`: V-component of wind at 10m

**Returns:**
- `str`: The filename of the saved PNG image


**Example Usage:**

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

**Notes:**

- The function automatically calculates the optimal aspect ratio based on the geographic extent of the data
- Latitude distortion is corrected using cosine correction for accurate aspect ratio calculation
- The output image dimensions are calculated to maintain geographic proportions
- The function includes coastlines, borders, and land features from Cartopy
- When using streamlines, white-colored streams are overlaid on the heatmap. This functionality is aimed to be a double-check of the wind results generated on VectorFieldAnimation module.
- The function uses `plt.tight_layout()` and `bbox_inches='tight'` for optimal spacing
- Final pixel dimensions and save confirmation are printed to console

## VectorFieldAnimation

The `VectorFieldAnimation` class creates dynamic visualizations of wind data from ERA5 datasets by combining background images ([Base Plot Module](#base-plot)) with animated streamlines representing wind flow patterns. It offers a clean, method-chaining interface for configuring various aspects of the animation including background images, streamlines, titles, and colorbars.

### Class

```python
class VectorFieldAnimation(dataset=None, background_image_path=None)

```
Initialize the animation configuration. The initialization above is one of the many ways to initialize the class, however, VectorFieldAnimatio provides methods to set the dataset and background, which is highly encourage to use. 


**Parameters:**

- `dataset` ([xr.Dataset]): Xarray Dataset containing wind data.
- `background_image_path` (Path[str]): Path to background image.

**Example:**
```python
# Basic initialization
animation = VectorFieldAnimation()

# With initial dataset and background
animation = VectorFieldAnimation(
    dataset=wind_dataset,
    background_image_path="background.png"
)

## By using class methods.

vf.set_dataset(your_dataset)

# Create the background image and set under the hood
vf.create_background_image(
    dict_extract_var=dict_extract_var,
    var_heatmap = 'wind_speed' 
)
```

### Methods

#### **Dataset Management**:

#### `set_dataset(dataset)`
Set the wind dataset for the animation.

**Parameters:**
- `dataset` (xr.Dataset): xarray Dataset with: u10, v10, latitude, longitude variables

#### `dataset()`
Get the current dataset.

**Returns:**
- `Optional[xr.Dataset]`: The current dataset or None

---

#### **Background Image Management**

#### `set_background_image(image_path)`
Set the path to the background image.

**Parameters:**
- `image_path` (str | Path): Relative path to the background image

**Returns:**
- `VectorFieldAnimation`: Self for method chaining

#### `get_background_image_path()`
Get the current background image path.

**Returns:**
- `Optional[Path]`: The current background image path

#### `create_background_image(dict_extract_var, **kwargs)`
Generate a base image for the plot and set it as the background image. This method is the same as using the function present at the Base Plot module: [create_layer_base](#create_layer_base)

**Parameters:**

- `dict_extract_var` (Dict): Dictionary containing 'long', 'lat', and variable data
- `var_heatmap` (str): Variable for heatmap (default: 'wind_speed')
- `cmap` (str): Colormap for heatmap (default: 'plasma_r')
- `crs_transform` (cartopy.crs.Projection): Coordinate reference system (default: PlateCarree)
- `dpi` (int): Resolution in dots per inch (default: 300)
- `height_inches` (int): Figure height in inches (default: 7)
- `stream_lines` (bool): Include streamlines (default: False)
- `dataset_subsampled` (xr.Dataset): Subsampled data for streamlines (required if stream_lines=True)
- `kwargs_streamplot`: Additional streamplot arguments

---

#### **Configuration Methods**

####  `configure_baseplot()`

Controls the height of the background image within Manim scene. 

**Parameters:**

- `image_height` (`float`, default: `7`): Height of the background image in Manim units. Should be less than the Manim canvas height (default is 8)


#### `configure_title(**kwargs)`
Configure title display and styling.

**Parameters:**

- `show_title` (bool): Whether to show title (default: False)
- `title_text` (str): Title text (default: None)
- `font_size` (int): Font size (default: 36)
- `title_color` (ManimColor): Title color (default: WHITE)

#### `configure_subtitle(**kwargs)`
Configure subtitle display and styling.

**Parameters:**

- `show_suptitle` (bool): Whether to show subtitle (default: False)
- `suptitle_text` (str): Subtitle text (default: None - uses date/time of wind data)
- `font_size` (int): Font size
- `suptitle_color` (ManimColor): Subtitle color (default: WHITE)

**Returns:**
- `VectorFieldAnimation`: Self for method chaining

#### `configure_streamplot(**kwargs)`
Configure streamline animation parameters. One of the cores of Lombricquiver library. It controls **ALL** aspects of the streamline animation behavior and appearance.

```python
animator.configure_streamplot(
    delta_y=0.15,
    resize_factor=0.05,
    stroke_width=1.0,
    flow_speed=2.0,
    time_width=0.3,
    animation_duration=3,
    dt=0.01,
    max_anchors_per_line=100,
    color="WHITE",
    virtual_time=4
)
```
**Grid and Positioning:**

- **delta_y** (`float`, default: `0.15`): Step size for the streamline grid placement. Larger values create more spacing between streamlines but reduce accuracy. Too small values can cause performance issues.
Linspace of the x & y axis. (default is 0.15). It is the step size for the linspace of the x and y axis. A component for placing the streamlines agents. As bigger the linspace, as more space the agents and less accuracy on placement. However, it is not recommended to set it too small, as it can lead to performance issues.
- **resize_factor** (`float`, default: `0.05`): Proportion to resize the streamlines relative to the background image. A value of 0.05 means streamlines cover 95% of the image area

**Visual Appearance:**

- **stroke_width** (`float`, default: `1.0`): Width of the streamlines in Manim units
- **color** (`str`, default: `"WHITE"`): Color of the streamlines

**Animation Behavior:**

- **flow_speed** (`float`, default: `2.0`):  Speed of the flow animation. It is the speed of the streamlines animation in Manim units per second.
- **time_width** (`float`, default: `0.3`): Proportion of each streamline visible during animation (0.0 to 1.0)
- **animation_duration** (`float`, default: `3`): Total duration to wait after animation starts (in seconds). This is applied to the Scene class method `wait()`. Which is the time the scene will wait after the animation has started. (default is 3). It is directly the duration of animation after the agents movents has started.
- **virtual_time** (`float`, default: `4`): Total time agents move in the vector field. Higher values create longer streamlines. The time the agents get to move in the vector field. Higher values therefore result in longer stream lines
            Virtual time for the animation (default is 4). This is computed at the Scene level, not on the construction method. Read Manim documentation for more details.
        

**Technical Parameters:**

- **dt** (`float`, default: `0.01`): Time step factor for agent movement. Lower values provide better trajectory approximation but may impact performance. A scalar to the amount the agent object is moved along the vector field. The actual distance is based on the magnitude of the vector field.
            Therefore, it is the factor by which the distance an agent moves per step is stretched. Lower values result in a better approximation of the trajectories in the vector field.
- **max_anchors_per_line** (`int`, default: `100`): Maximum number of anchor points per streamline. More anchors increase accuracy but may reduce performance. Maximum number of anchors per stream line (default is 100). It is the maximum number of anchors per stream line in the streamlines animation.
            Manim creates anchors to position the streamlines agents. The more anchors, the more accurate the streamlines will be, but it can lead to performance issues.

Note: 
- All these parameters belongs to the class [Streamline()](https://docs.manim.community/en/stable/reference/manim.mobject.vector_field.StreamLines.html), which is a Manim MObject class. More details of its functioning can be retrieved at on the Manim Community.




#### `configure_colorbar(**kwargs)`
Configure colorbar appearance and data mapping.

**Parameters:**

- `palette` (str | matplotlib.colors.Colormap | list): Color palette/colormap
- `num_colors` (int): Number of colors to extract from palette
- `data_min` (float): Minimum data value (default: 0)
- `data_max` (float): Maximum data value (default: num_colors)


#### **Utility Methods**

#### `is_ready()`
Check if the animation configuration is complete and ready for creation.

#### `get_missing_requirements()`
Get a list of missing configuration requirements.

#### `get_scene_class()`
Get a configured Scene class ready for Manim.

#### `preview_config()`
Get a preview of the current configuration.

---


## Technical Notes

- The class uses an internal `VectorFieldConfig` object to store configuration
- Background images are automatically saved as 'base_layer.png' when using `create_background_image()`
- All configuration methods return `self` to enable method chaining
- The final scene class extends `StreamPlot` with the configured parameters

**Coordinate System**:

- The class automatically handles transformations between geographic coordinates (latitude/longitude) and Manim's screen coordinate system.
- Streamlines are automatically scaled and positioned to fit within the background image boundaries.
- Currently, there is a limitation regarding CRS transformation and polar plots. The library does not support transformations and the main CRS adopted is: ccrs.PlateCarree().Please few free to contribute to the project in case of implementing CRS transformations. 

**Performance Considerations**:

- Lower `delta_y` values provide more detailed streamlines but require more computational resources! 
- Higher `max_anchors_per_line` values increase accuracy but may slow rendering.
- `dt` parameter affects both accuracy and performance - very small values may cause slowdowns.

**Data Requirements**:

- ERA5 datasets should have consistent coordinate naming (`latitude`, `longitude`, `u10`, `v10`, `valid_time`).
- Background images should have sufficient resolution for the desired output quality.
- Coordinate ranges in the dataset should match the geographic area shown in the background image.

