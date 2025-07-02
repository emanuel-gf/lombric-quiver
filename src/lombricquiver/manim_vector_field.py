from dataclasses import dataclass
from pathlib import Path
import numpy as np
import pandas as pd
from manim import Scene, ImageMobject, FadeIn, StreamLines, WHITE, Text, UP, DOWN, LEFT, RIGHT, Group, ManimColor, BLUE
from scipy.interpolate import RegularGridInterpolator
import xarray as xr
from typing import Optional, Union, Tuple, List, Dict, Callable, Any
from .colormap import ColorPalette
from .base_map import create_layer_base



@dataclass
class BasePlotConfig:
    """Configuration for base plot settings."""
    image_height: float = 7.0

@dataclass
class TitleConfig:
    """Configuration for title display."""
    show_title: bool = False
    title_text: str = "ERA5 Wind - Vector Data"
    title_font_size: int = 36
    title_color: str = WHITE

@dataclass
class SubtitleConfig:
    """Configuration for subtitle display."""
    show_suptitle: bool = False
    suptitle_text: str = 'Lorem ipsum'
    font_size: int = 24
    suptitle_color: str = WHITE

@dataclass
class StreamPlotConfig:
    """Configuration for stream plot parameters.
     **Streamplot Config**:    
        delta_y : float
            Linspace of the x & y axis. (default is 0.15). It is the step size for the linspace of the x and y axis. A component for placing the streamlines agents. As bigger the 
            the linspace, as more space the agents and less accuracy on placement. However, it is not recommended to set it too small, as it can lead to performance issues.
        resize_factor : float
            Resize factor for the streamplot (default is 0.05). It is used to resize the streamlines to fit within the base plot. If 0.05 as default, the streamlines will have
            a heightxwidth of 95% of the base plot. 
        stroke_width : float   
            Width of the stream lines (default is 1.0). It is the width of the streamlines in Manim units.
        flow_speed : float
            Speed of the flow animation (default is 2.0). It is the speed of the streamlines animation in Manim units per second.
        time_width : float
            The proportion of the stream line shown while being animated. (default is 0.3)
        animation_duration : float
            This is applied to the Scene class method `wait()`. Which is the time the scene will wait after the animation has started. (default is 3).
            It is the duration of animation after the agents movents has started.
        dt : float
            A scalar to the amount the agent object is moved along the vector field. The actual distance is based on the magnitude of the vector field.
            Therefore, it is the factor by which the distance an agent moves per step is stretched. Lower values result in a better approximation of the trajectories in the vector field.
        max_anchors_per_line : int
            Maximum number of anchors per stream line (default is 100). It is the maximum number of anchors per stream line in the streamlines animation.
            Manim creates anchors to position the streamlines agents. The more anchors, the more accurate the streamlines will be, but it can lead to performance issues.
        color : str
            Color of the stream lines (default is WHITE). It is the color of the streamlines in Manim.
        virtual_time : float
            The time the agents get to move in the vector field. Higher values therefore result in longer stream lines
            Virtual time for the animation (default is 4). This is computed at the Scene level, not on the construction method. Read Manim documentation for more details.
        
    Color: ManimColor
        It should be an object of ManimColor. It does not accept hex colors unless it being passed as ManimColor(#fffff) """
    
    delta_y: float = 0.15
    resize_factor: float = 0.04
    stroke_width: float = 1.0
    flow_speed: float = 2.0
    time_width: float = 0.3
    animation_duration: float = 4.0
    dt: float = 0.03
    max_anchors_per_line: int = 50
    color: str = WHITE
    virtual_time: float = 4.0

@dataclass
class ColorbarConfig:
    """Configuration for colorbar settings."""
    show: bool = False
    palette: Optional[Union[str,List[str]]] = 'discrete1'
    num_colors: int = 4
    title: Optional[str] = None
    title_size: int = 12
    label_size: int = 16
    width_ratio: float = 0.8
    figsize: Tuple[int, int] = (2, 8)


class VectorFieldConfig:
    """
    Configuration container for vector field animations.
    Encapsulates all configuration parameters.
    """
    
    def __init__(self):
        self.baseplot = BasePlotConfig()
        self.title = TitleConfig()
        self.subtitle = SubtitleConfig()
        self.streamplot = StreamPlotConfig()
        self.colorbar = ColorbarConfig()
        
        # Data storage
        self._dataset: Optional[xr.Dataset] = None
        self._background_image_path: Optional[Path] = None
    
    @property
    def dataset(self) -> Optional[xr.Dataset]:
        """Get the current dataset."""
        return self._dataset
    
    @dataset.setter
    def dataset(self, value: xr.Dataset) -> None:
        """Set the dataset with validation."""
        if not isinstance(value, xr.Dataset):
            raise TypeError("Dataset must be an xarray Dataset")
        
        required_vars = ['latitude', 'longitude','lat','lon','long']
        missing_vars = [var for var in value.variables if var in required_vars]
        if len(missing_vars)!=2:
            raise ValueError(f"Any of the following variables are missing: {missing_vars}. Check the name of the lat,lon variables on xr.Dataset")
        
        self._dataset = value
    
    @property
    def background_image_path(self) -> Optional[Path]:
        """Get the background image path."""
        return self._background_image_path
    
    @background_image_path.setter
    def background_image_path(self, value: str | Path) -> None:
        """Set the background image path with validation."""
        path = Path(value)
        if not path.exists():
            raise FileNotFoundError(f"Background image not found: {path}")
        self._background_image_path = path
    
    def is_ready(self) -> bool:
        """Check if configuration is ready for animation."""
        return self._dataset is not None and self._background_image_path is not None
    
    def get_missing_requirements(self) -> list:
        """Get list of missing requirements."""
        missing = []
        if self._dataset is None:
            missing.append("dataset")
        if self._background_image_path is None:
            missing.append("background_image_path")
        return missing


class StreamPlot(Scene):
    """
    Manim Scene class for creating wind vector field animations.
    
    This class should be used with a properly configured VectorFieldConfig instance.
    """
    
    def __init__(self, config: VectorFieldConfig, **kwargs):
        super().__init__(**kwargs)
        self.config = config
        if not self.config.is_ready():
            missing = self.config.get_missing_requirements()
            raise ValueError(f"Configuration not ready. Missing: {missing}")
        
        # Cache for data processing
        self._u_interp: Optional[RegularGridInterpolator] = None
        self._v_interp: Optional[RegularGridInterpolator] = None
        self._wind_data_cache: Optional[Tuple] = None
    
    def construct(self):
        """Construct the animation scene."""
        # Update subtitle with timestamp if enabled
        if self.config.subtitle.show_suptitle:
            timestamp = pd.to_datetime(str(self.config.dataset['valid_time'].values))
            self.config.subtitle.suptitle_text = timestamp.strftime('%Y-%m-%d %H:%M:%S')
            print(self.config.subtitle.suptitle_text)
        
        if self.config.colorbar.show:
            self._construct_colored_streamplot()
        else:
            self._construct_simple_streamplot()
    
    def _construct_simple_streamplot(self):
        """Construct streamplot with single color."""
        # Load and setup background image
        geo_image = self._setup_background_image()
        
        # Get image dimensions and coordinate mappings
        img_dims = self._get_image_dimensions(geo_image)
        
        # Create wind vector function - Map scene coordinates to 
        wind_vector_func = self._create_wind_vector_function(**img_dims)
        
        # Create streamlines with single color
        stream_lines = self._create_single_color_streamlines(
            wind_vector_func,
            geo_image,
            color=self.config.streamplot.color
        )
        
        # Group elements
        elements = Group()
        elements.add(geo_image, stream_lines)
        
        # Add titles and suptitle if show==True
        self._add_titles(elements)
        
        # Start Animation and wait()
        self._animate_streamlines(stream_lines)
    
    def _construct_colored_streamplot(self):
        """Construct streamplot with color mapping."""
        # Load and setup background image
        geo_image = self._setup_background_image()
        
        # Get image dimensions and coordinate mappings
        img_dims = self._get_image_dimensions(geo_image)
        
        # Create wind functions
        wind_vector_func = self._create_wind_vector_function(**img_dims)
        wind_color_func = self._create_wind_color_function(**img_dims)
        
        # Get wind speed range
        min_wind_speed = self.config.dataset['wind_speed'].values.min()
        max_wind_speed = self.config.dataset['wind_speed'].values.max()
        
        # Create color palette  - depending if an array or the palette name is given 
        color_palette = self._create_color_palette(self.config.colorbar.palette,
                                                   self.config.colorbar.num_colors,
                                                    min_wind_speed,
                                                    max_wind_speed)
        
        ## Parse the hex colors to manim colors  
        manim_colors = [ManimColor(hex_color) for hex_color in color_palette]
        
        
        # Create colored streamlines
        stream_lines = self._create_colored_streamlines(
            wind_vector_func=wind_vector_func,
            image=geo_image, 
            color_scheme=wind_color_func,
            colors=manim_colors,
            min_color_value=int(min_wind_speed),
            max_color_value=int(max_wind_speed)
        )
        
        # Group elements
        vg_streamline = Group(geo_image, stream_lines)
        
        # Add titles that alings with the Group object
        self._add_titles(vg_streamline)
        
        # Add colorbar
        self._add_colorbar(vg_streamline)
        
        # Start animation
        self._animate_streamlines(stream_lines)
    
    def _create_color_palette(self, palette, num_colors, min_wind_speed, max_wind_speed):
        """Creates an instance of ColorPalette class. 

        Args:
        palette : str, matplotlib.colors.Colormap, or list
            The color palette/colormap name (e.g., 'viridis', 'tab10'), 
            colormap object, or list of hex color strings
        num_colors : int, optional
            Number of colors to extract from the palette. 
            If palette is a list, this defaults to len(palette)
        data_min : float, optional
            Minimum data value. If None, defaults to 0
        data_max : float, optional
            Maximum data value. If None, defaults to num_colors

        Returns:
            hex_colors: An array of hex colors
        """
        ## create the instance
        colorpalette = ColorPalette(palette = self.config.colorbar.palette,
                                    num_colors = self.config.colorbar.num_colors,
                                    data_min= min_wind_speed,
                                    data_max= max_wind_speed)
        
        ## save the colorbar plot with right parameters
        colorpalette.save_plot( width_ratio = self.config.colorbar.width_ratio,
                                title = self.config.colorbar.title,
                                title_size=self.config.colorbar.title_size,
                                label_size=self.config.colorbar.label_size,
                                figsize=self.config.colorbar.figsize
                                )

        return colorpalette.get_hex_colors()
             
    def _setup_background_image(self) -> ImageMobject:
        """Setup and add background image."""
        geo_image = ImageMobject(str(self.config.background_image_path))
        geo_image.height = self.config.baseplot.image_height
        geo_image.center()
        self.add(geo_image)
        return geo_image
    
    def _get_image_dimensions(self, geo_image: ImageMobject) -> Dict[str, float]:
        """Get image dimensions and coordinate mappings."""
        return {
            'x_min': geo_image.get_left()[0],
            'x_max': geo_image.get_right()[0],
            'y_min': geo_image.get_bottom()[1],
            'y_max': geo_image.get_top()[1]
        }
    
    def _create_single_color_streamlines(self, wind_vector_func: Callable, geo_image: ImageMobject,
                                       color: str = None) -> StreamLines:
        """Create streamlines with a single color."""
        
        ## Matches the width and height of the background image.
        img_width = geo_image.width
        img_height = geo_image.height
        
        # Calculate ranges regarding the resize factor
        x_range_min = (img_width - img_width * self.config.streamplot.resize_factor) / 2
        y_range_min = (img_height - img_height * self.config.streamplot.resize_factor) / 2
        
        # Parameters for single color streamlines
        streamlines_params = {
            'func': wind_vector_func,
            'x_range': [-x_range_min, x_range_min, self.config.streamplot.delta_y],
            'y_range': [-y_range_min, y_range_min, self.config.streamplot.delta_y],
            'dt': self.config.streamplot.dt,
            'padding': 0,
            'noise_factor': 0.0,
            'max_anchors_per_line': self.config.streamplot.max_anchors_per_line,
            'stroke_width': self.config.streamplot.stroke_width,
            'virtual_time': self.config.streamplot.virtual_time,
            'color': self.config.streamplot.color
        }
        
        stream_lines = StreamLines(**streamlines_params)
        stream_lines.center()
        self.add(stream_lines)
        
        return stream_lines
    
    def _create_colored_streamlines(self, wind_vector_func: Callable, image: ImageMobject,
                                  color_scheme: Callable, colors: list, 
                                  min_color_value: float, max_color_value: float) -> StreamLines:
        """Create streamlines with color mapping based on a color scheme."""
        img_width = image.width
        img_height = image.height
        
        # Calculate ranges
        x_range_min = (img_width - img_width * self.config.streamplot.resize_factor) / 2
        y_range_min = (img_height - img_height * self.config.streamplot.resize_factor) / 2
        
        # Parameters for colored streamlines
        streamlines_params = {
            'func': wind_vector_func,
            'x_range': [-x_range_min, x_range_min, self.config.streamplot.delta_y],
            'y_range': [-y_range_min, y_range_min, self.config.streamplot.delta_y],
            'dt': self.config.streamplot.dt,
            'padding': 0,
            'noise_factor': 0.0,
            'max_anchors_per_line': self.config.streamplot.max_anchors_per_line,
            'stroke_width': self.config.streamplot.stroke_width,
            'virtual_time': self.config.streamplot.virtual_time,
            'color_scheme': color_scheme,
            'colors': colors,
            'min_color_scheme_value': min_color_value,
            'max_color_scheme_value': max_color_value
        }
        
        stream_lines = StreamLines(**streamlines_params)
        stream_lines.center()
        self.add(stream_lines)
        
        return stream_lines
    
    def _add_titles(self, vg_streamline: Group):
        """Add title and subtitle if configured."""
        title = None
        
        # Add main title
        if self.config.title.show_title:
            title = Text(
                self.config.title.title_text,
                font_size=self.config.title.title_font_size,
                color=self.config.title.title_color
            )
            self.add(title.next_to(vg_streamline, UP, buff=0.02))
        
        # Add subtitle
        if self.config.subtitle.show_suptitle:
            suptitle = Text(
                self.config.subtitle.suptitle_text,
                font_size=self.config.subtitle.font_size,
                color=self.config.subtitle.suptitle_color
            )
            
            self.add(suptitle.next_to(vg_streamline,LEFT,buff=0.2))
            
            # if title is not None:
            #     suptitle.next_to(title, DOWN, buff=0.5)
            # else:
            #     suptitle.to_edge(LEFT)

    
    def _add_colorbar(self, vg_streamline: Group):
        """Add colorbar to the scene."""
        # This assumes colorbar.png is created elsewhere
        colorbar_path = Path('colorbar.png')
        if colorbar_path.exists():
            colorbar_img = ImageMobject('colorbar.png')
            
            # get width of group
            width_ = vg_streamline.width
            colorbar_img.height = vg_streamline.height
            colorbar_img.width = 0.5 #round(width_/15,1) # It width is 1/15 of the whole background width
            print('colorbar settings on scene',colorbar_img.width,colorbar_img.height)
            self.add(colorbar_img.next_to(vg_streamline, RIGHT, buff=0.04))
    
    def _animate_streamlines(self, stream_lines: StreamLines):
        """Start streamlines animation."""
        stream_lines.start_animation(
            warm_up=False,
            flow_speed=self.config.streamplot.flow_speed,
            time_width=self.config.streamplot.time_width
        )
        self.wait(self.config.streamplot.animation_duration)
    
    def _extract_wind_data(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Extract wind data from dataset."""
        if self._wind_data_cache is None:
            u10 = self.config.dataset['u10'].values
            v10 = self.config.dataset['v10'].values
            lats = self.config.dataset['latitude'].values
            lons = self.config.dataset['longitude'].values
            self._wind_data_cache = (u10, v10, lats, lons)
        
        return self._wind_data_cache
    
    def _create_interpolators(self) -> Tuple[RegularGridInterpolator, RegularGridInterpolator]:
        """Create interpolators for wind components."""
        if self._u_interp is None or self._v_interp is None:
            u10, v10, lats, lons = self._extract_wind_data()
            
            # Ensure arrays are in correct order for interpolation
            if lats[0] > lats[-1]:
                lats = lats[::-1]
                u10 = u10[::-1, :]
                v10 = v10[::-1, :]
            if lons[0] > lons[-1]:
                lons = lons[::-1]
                u10 = u10[:, ::-1]
                v10 = v10[:, ::-1]
            
            self._u_interp = RegularGridInterpolator((lats, lons), u10)
            self._v_interp = RegularGridInterpolator((lats, lons), v10)
        
        return self._u_interp, self._v_interp
    
    def _create_wind_vector_function(self, x_min: float, x_max: float, 
                                   y_min: float, y_max: float) -> Callable:
        """Create wind vector function for streamlines.
        
        It maps screen coordinats to geographic coordinates and return the u and v vectors for the requested point"""
        
        u_interp, v_interp = self._create_interpolators()
        _, _, lats, lons = self._extract_wind_data()
        
        def wind_vector_func(pos: np.ndarray) -> np.ndarray:
            x, y = pos[0], pos[1]
            # Map from screen coordinates to geographic coordinates
            lon = np.interp(x, [x_min, x_max], [lons.min(), lons.max()])
            lat = np.interp(y, [y_min, y_max], [lats.min(), lats.max()])
            
            try:
                u = u_interp([lat, lon])[0]
                v = v_interp([lat, lon])[0]
                return np.array([u, v, 0.0])
            except:
                return np.array([0.0, 0.0, 0.0])
        
        return wind_vector_func
    
    def _create_wind_color_function(self, x_min: float, x_max: float,
                                  y_min: float, y_max: float) -> Callable:
        """Create wind color function for colored streamlines."""
        u_interp, v_interp = self._create_interpolators()
        _, _, lats, lons = self._extract_wind_data()
        
        def wind_color_func(pos: np.ndarray) -> float:
            x, y = pos[0], pos[1]
            lon = np.interp(x, [x_min, x_max], [lons.min(), lons.max()])
            lat = np.interp(y, [y_min, y_max], [lats.min(), lats.max()])
            
            try:
                u = u_interp([lat, lon])[0]
                v = v_interp([lat, lon])[0]
                return np.linalg.norm([u, v])
            except:
                return 0.0
        
        return wind_color_func       

        
class VectorFieldAnimation:
    """
    Main interface class for creating vector field animations.
    
    This class provides a clean, fluent API for configuring and creating
    vector field animations with Manim.
    
    Example:
    --------
    animation = VectorFieldAnimation()
    animation.set_dataset(your_dataset) \
             .set_background_image("path/to/image.png") \
             .configure_title(show_title=True, title_text="My Wind Plot") \
             .configure_streamplot(flow_speed=3.0, animation_duration=5.0)
    
    scene_class = animation.get_scene_class()
    """
    
    def __init__(self, dataset: Optional[xr.Dataset] = None, 
                 background_image_path: Optional[str] = None):
        """
        Initialize the animation configuration.
        
        Args:
            dataset: Optional xarray Dataset containing wind data
            background_image_path: Optional path to background image
        """
        self.config = VectorFieldConfig()
        
        if dataset is not None:
            self.set_dataset(dataset)
        if background_image_path is not None:
            self.set_background_image(background_image_path)
    
    def set_dataset(self, dataset: xr.Dataset) -> 'VectorFieldAnimation':
        """
        Set the wind dataset.
        
        Args:
            dataset: xarray Dataset with u10, v10, latitude, longitude variables
            
        Returns:
            Self for method chaining
        """
        self.config.dataset = dataset
        return self
    
    def dataset(self) -> Optional[xr.Dataset]:
        return self.config.dataset
    
    def set_background_image(self, image_path: str | Path) -> 'VectorFieldAnimation':
        """It stores the path of the image. 

        Args:
            image_path (str | Path): relative Path

        """
        self.config.background_image_path = image_path
        print("All good, background image path set to:", self.config.background_image_path)
        return self
    
    def get_background_image_path(self) -> Optional[Path]:
        """Get the current background image path."""
        print(self.config.background_image_path)
        return self.config.background_image_path
    
    def create_background_image(self, dict_extract_var: Dict, **kwargs) -> 'VectorFieldAnimation':
        """
        Generate a base image for the plot. And set it as the attr background_image
        
        Args:
            dict_extract_var: Dictionary containing 'long', 'lat', and variable data
            var_heatmap (str): The variable to be used for the heatmap. By default, it is set to 'wind_speed'. It should be a key in the `dict_extract_var` dictionary.
            cmap (str): Colormap for the heatmap. By default, it is set to 'plasma_r'. Refers to https://matplotlib.org/stable/gallery/color/colormap_reference.html 
            crs_transform (cartopy.crs.Projection): The coordinate reference system for the plot. By default, it is set to PlateCarree. It can be any valid Cartopy projection, such as `ccrs.Mercator()`, `ccrs.LambertConformal()`, etc.
            dpi (int): Dots per inch for the figure resolution. By default, it is set to 100.
            height_inches (int): Height of the figure in inches. By default, it is set to 9 inches. This height is highly related with Manim canvas.
            stream_lines (bool): Whether to include streamlines in the plot.   By default, it is set to False.
            dataset_subsampled (xr.dataset): xarray dataset containing subsampled data for streamlines. Only required if `stream_lines` is True.
            kwargs_streamplot: Additional keyword arguments for the streamplot function, such as `density`, `linewidth`, etc.
    
        Returns:
            Self for method chaining
        """
        default_params = {
            'var_heatmap': 'wind_speed',
            'dpi': 300,
            'height_inches': 7,
            'cmap': 'plasma_r',
            'stream_lines': False,
        }
        default_params.update(kwargs)
        
        # Call the function to create the layer base
        create_layer_base(dict_extract_var, **default_params)
        
        self.set_background_image('base_layer.png')
        
        return self
    
    def configure_baseplot(self, **kwargs) -> 'VectorFieldAnimation':
        """Configure the height of the baseplot to be exhibit in Manim Scene. Even though your image is created with
        a certain height, it will be scaled in Manim to fit the canvas, which by default is 8.0 Manim Units. However
        by configuring the baseplot height, you can change the height of the image in Manim scene
        and it can never be bigger than the Manim Scene by itself.
        
        Parameters:
        image_height: float
            Height of the base plot image in Manim units. Default is 7.0."""
        for key, value in kwargs.items():
            if hasattr(self.config.baseplot, key):
                setattr(self.config.baseplot, key, value)
        return self
    
    def configure_title(self, **kwargs) -> 'VectorFieldAnimation':
        """Parameters:
        show_title: Bool
            Either expose or not the title. Default (False)
        title_text: Str
            Title Text. Default if None
        font_size: int
            Default 36.
        title_color: ManimColor
            Default WHITE
            """
        for key, value in kwargs.items():
            if hasattr(self.config.title, key):
                setattr(self.config.title, key, value)
        return self
    
    def configure_subtitle(self, **kwargs) -> 'VectorFieldAnimation':
        """Parameters:
        'show_suptitle': Bool,
            Wheter show or not. Default False
        'suptitle_text': str
            If None, the given return is the date and time of the current wind data.
        'font_size': int
            font size
        'suptitle_color': ManimColor
            Default WHITE
        """        
        
        for key, value in kwargs.items():
            if hasattr(self.config.subtitle, key):
                setattr(self.config.subtitle, key, value)
        return self
    
    def configure_streamplot(self, **kwargs) -> 'VectorFieldAnimation':
        """
         **Streamplot Config**:    
        delta_y : float
            Linspace of the x & y axis. (default is 0.15). It is the step size for the linspace of the x and y axis. A component for placing the streamlines agents. As bigger the 
            the linspace, as more space the agents and less accuracy on placement. However, it is not recommended to set it too small, as it can lead to performance issues.
        resize_factor : float
            Resize factor for the streamplot (default is 0.05). It is used to resize the streamlines to fit within the base plot. If 0.05 as default, the streamlines will have
            a heightxwidth of 95% of the base plot. 
        stroke_width : float   
            Width of the stream lines (default is 1.0). It is the width of the streamlines in Manim units.
        flow_speed : float
            Speed of the flow animation (default is 2.0). It is the speed of the streamlines animation in Manim units per second.
        time_width : float
            The proportion of the stream line shown while being animated. (default is 0.3)
        animation_duration : float
            This is applied to the Scene class method `wait()`. Which is the time the scene will wait after the animation has started. (default is 3).
            It is the duration of animation after the agents movents has started.
        dt : float
            A scalar to the amount the agent object is moved along the vector field. The actual distance is based on the magnitude of the vector field.
            Therefore, it is the factor by which the distance an agent moves per step is stretched. Lower values result in a better approximation of the trajectories in the vector field.
        max_anchors_per_line : int
            Maximum number of anchors per stream line (default is 100). It is the maximum number of anchors per stream line in the streamlines animation.
            Manim creates anchors to position the streamlines agents. The more anchors, the more accurate the streamlines will be, but it can lead to performance issues.
        color : str
            Color of the stream lines (default is WHITE). It is the color of the streamlines in Manim.
        virtual_time : float
            The time the agents get to move in the vector field. Higher values therefore result in longer stream lines
            Virtual time for the animation (default is 4). This is computed at the Scene level, not on the construction method. Read Manim documentation for more details.
        
        """
        
        for key, value in kwargs.items():
            if hasattr(self.config.streamplot, key):
                setattr(self.config.streamplot, key, value)
        return self
    
    def configure_colorbar(self, **kwargs) -> 'VectorFieldAnimation':
        """Parameters:
        -----------
        palette : str, matplotlib.colors.Colormap, or list
            The color palette/colormap name (e.g., 'viridis', 'tab10'), 
            colormap object, or list of hex color strings
        num_colors : int, optional
            Number of colors to extract from the palette. 
            If palette is a list, this defaults to len(palette)
        data_min : float, optional
            Minimum data value. If None, defaults to 0
        data_max : float, optional
            Maximum data value. If None, defaults to num_colors"""
        for key, value in kwargs.items():
            if hasattr(self.config.colorbar, key):
                setattr(self.config.colorbar, key, value)
        return self
    
    def is_ready(self) -> bool:
        """Check if the animation is ready to be created."""
        return self.config.is_ready()
    
    def get_missing_requirements(self) -> list:
        """Get list of missing requirements."""
        return self.config.get_missing_requirements()
    
    def get_scene_class(self) -> type:
        """
        Get a configured Scene class ready for Manim.
        
        Returns:
            A Scene class that can be used with Manim
        """
        if not self.is_ready():
            missing = self.get_missing_requirements()
            raise ValueError(f"Animation not ready. Missing: {missing}")
        
        config = self.config
        
        class ConfiguredStreamPlot(StreamPlot):
            def __init__(self, **kwargs):
                super().__init__(config, **kwargs)
        
        return ConfiguredStreamPlot
    
    def preview_config(self) -> Dict[str, Any]:
        """Get a preview of the current configuration."""
        return {
            'dataset_set': self.config.dataset is not None,
            'background_image_set': self.config.background_image_path is not None,
            'ready': self.is_ready(),
            'streamplot':{
                'delta_y':self.config.streamplot.delta_y,
                'resize_factor':self.config.streamplot.resize_factor,
                'stroke_width':self.config.streamplot.stroke_width,
                'flow_speed':self.config.streamplot.flow_speed,
                'time_width':self.config.streamplot.time_width,
                'animation_duration':self.config.streamplot.animation_duration,
                'dt':self.config.streamplot.dt,
                'max_anchors_per_line': self.config.streamplot.max_anchors_per_line,
                'color':self.config.streamplot.color,
                'virtual_time':self.config.streamplot.virtual_time
                },
            'title': {
                'show': self.config.title.show_title,
                'text': self.config.title.title_text,
                'title_size': self.config.title.title_size,
            },
            'subtitle': {
                'show': self.config.subtitle.show_suptitle,
                'text': self.config.subtitle.suptitle_text,
                'text_size': self.config.subtitle.text_size,
            },
            'colorbar': {
                'show': self.config.colorbar.show,
                'palette_name': self.config.colorbar.palette_name,
                'palette_array':self.config.colorbar.palette_array is not None,
                'num_colors':  self.config.colorbar.num_colors,
                'title':self.config.colorbar.title,
                'title_size':self.config.colorbar.title_size,
                'label_size': self.config.colorbar.label_size,
                'width_ratio':self.config.colorbar.width_ratio
            }
        }
        
