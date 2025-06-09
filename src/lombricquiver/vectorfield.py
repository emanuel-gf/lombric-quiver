import numpy as np
import pandas as pd
from manim import Scene, ImageMobject, FadeIn, StreamLines, WHITE, Text, UP, DOWN, LEFT, RIGHT
from manim import config as manim_config
from manim.utils.ipython_magic import ManimMagic
from scipy.interpolate import RegularGridInterpolator
import xarray as xr
import os
import tempfile
from IPython.display import display, HTML, Video

class StreamPlot(Scene):
    """
    Manim Scene class for creating wind vector field animations.
    
    This class is created over the Scene Class of Manim. It is a constructor for the scene.
    This class can be used directly with Manim magic commands:
    %manim -ql -v WARNING StreamPlot
    
    Before using, make sure to configure the scene using VectorFieldConfig:
    
    Example:
    --------
    # Set up your data and configuration
    VectorFieldConfig.set_dataset(your_dataset)
    VectorFieldConfig.set_background_image("path/to/image.png")
    VectorFieldConfig.configure_title(show_title=True, title_text="My Wind Plot")
    
    # Then use the magic command
    %manim -ql -v WARNING StreamPlot
    """
    
    def construct(self):
        # Check if required data is available
        if VectorFieldConfig.DATASET is None:
            raise ValueError("Dataset is required. Set it with VectorFieldConfig.set_dataset()")
            
        if VectorFieldConfig.BACKGROUND_IMAGE_PATH is None:
            raise ValueError("Background image path is required. Set it with VectorFieldConfig.set_background_image()")
        
        # Update suptitle with dataset timestamp if enabled
        if VectorFieldConfig.CONFIG_SUPTITLE['show_suptitle']:
            VectorFieldConfig.CONFIG_SUPTITLE['suptitle_text'] = pd.to_datetime(
                str(VectorFieldConfig.DATASET['valid_time'].values)
            ).strftime('%Y-%m-%d %H:%M:%S')
        
        ## if-statement for dealing with colorized streamplot
        if not VectorFieldConfig.CONFIG_COLORBAR['show']:
            ## Create the scene for a single color streamplot
            
            # Load background image
            geo_image = ImageMobject(VectorFieldConfig.BACKGROUND_IMAGE_PATH)
            geo_image.height = VectorFieldConfig.CONFIG_BASEPLOT['image_height']
            geo_image.center()
            self.add(geo_image)  # Add directly without fade-in for magic command compatibility
            
            # Extract dimensions from ImageMobject
            img_width = geo_image.width
            img_height = geo_image.height
            x_min, x_max = geo_image.get_left()[0], geo_image.get_right()[0]
            y_min, y_max = geo_image.get_bottom()[1], geo_image.get_top()[1]
        
            # Extract wind data
            u10, v10, lats, lons = self._extract_wind_data()
            
            # Create interpolators
            u_interp, v_interp = self._create_interpolators(u10, v10, lats, lons)
            
            # Define wind vector function for the stream lines
            ## TODO implement a better architecture way for the following functions
            def wind_vector_func(pos):
                x, y = pos[0], pos[1]
                # Map from screen coordinates to geographic coordinates
                lon = np.interp(x, [x_min, x_max], [lons.min(), lons.max()])
                lat = np.interp(y, [y_min, y_max], [lats.min(), lats.max()])
                
                # Use interpolator
                try:
                    u = u_interp([lat, lon])[0]
                    v = v_interp([lat, lon])[0]
                except:
                    # Return zero vector if interpolation fails
                    return np.array([0.0, 0.0, 0.0])
                
                return np.array([u, v, 0.0])
            
            
            # Calculate the range of the streamline to match the ImageObject
            x_range_min = round((img_width - img_width * CONFIG_STREAMPLOT['resize_factor']), 2) / 2
            y_range_min = round((img_height - img_height * CONFIG_STREAMPLOT['resize_factor']), 2) / 2
            
            delta_y = CONFIG_STREAMPLOT['delta_y']
            
            # Create stream lines
            stream_lines = StreamLines(
                wind_vector_func,
                x_range=[-1 * x_range_min, x_range_min, delta_y],
                y_range=[-1 * y_range_min, y_range_min, delta_y],
                color=CONFIG_STREAMPLOT['color'],
                dt=CONFIG_STREAMPLOT['dt'],
                padding=0,
                noise_factor=0.0,
                max_anchors_per_line=CONFIG_STREAMPLOT['max_anchors_per_line'],
                stroke_width=CONFIG_STREAMPLOT['stroke_width'],
                virtual_time=CONFIG_STREAMPLOT['virtual_time']
            )
            
            # Center the stream lines
            stream_lines.center()
            self.add(stream_lines)
            
            ## group
            vg_streamline = VGroup(geo_image,stream_lines)
            
            
            # Add title if specified
            title = None
            if VectorFieldConfig.CONFIG_TITLE['show_title']:
                title = Text(
                    VectorFieldConfig.CONFIG_TITLE['title_text'],
                    font_size=VectorFieldConfig.CONFIG_TITLE['title_font_size'],
                    color=VectorFieldConfig.CONFIG_TITLE['title_color']
                )
                #title.to_edge(UP)
                self.add(title.next_to(vg_streamline, UP, buff=0.02))
                
                
            # Add subtitle if specified
            if VectorFieldConfig.CONFIG_SUPTITLE['show_suptitle']:
                suptitle = Text(
                    VectorFieldConfig.CONFIG_SUPTITLE['suptitle_text'],
                    font_size=VectorFieldConfig.CONFIG_SUPTITLE['suptitle_font_size'],
                    color=VectorFieldConfig.CONFIG_SUPTITLE['suptitle_color']
                )
                if title is not None:
                    suptitle.next_to(title, DOWN, buff=0.5)
                else:
                    suptitle.to_edge(UP)
                
            # Animate the stream lines
            stream_lines.start_animation(
                warm_up=False,
                flow_speed=VectorFieldConfig.CONFIG_STREAMPLOT['flow_speed'],
                time_width=VectorFieldConfig.CONFIG_STREAMPLOT['time_width']
            )
            
            self.wait(VectorFieldConfig.CONFIG_STREAMPLOT['animation_duration'])
        else:
            ## Create a scene with colorized stream plot
            
            # Load background image
            geo_image = ImageMobject(VectorFieldConfig.BACKGROUND_IMAGE_PATH)
            geo_image.height = VectorFieldConfig.CONFIG_BASEPLOT['image_height']
            geo_image.center()
            self.add(geo_image)  # Add directly without fade-in for magic command compatibility
            
            # Extract dimensions from ImageMobject
            img_width = geo_image.width
            img_height = geo_image.height
            x_min, x_max = geo_image.get_left()[0], geo_image.get_right()[0]
            y_min, y_max = geo_image.get_bottom()[1], geo_image.get_top()[1]
        
            # Extract wind data
            u10, v10, lats, lons = self._extract_wind_data()
            
            # Create interpolators
            u_interp, v_interp = self._create_interpolators(u10, v10, lats, lons)
            
            # Define wind vector function for the stream lines
            ## TODO implement a better architecture way for the following functions
            def wind_vector_func(pos):
                x, y = pos[0], pos[1]
                # Map from screen coordinates to geographic coordinates
                lon = np.interp(x, [x_min, x_max], [lons.min(), lons.max()])
                lat = np.interp(y, [y_min, y_max], [lats.min(), lats.max()])
                
                # Use interpolator
                try:
                    u = u_interp([lat, lon])[0]
                    v = v_interp([lat, lon])[0]
                except:
                    # Return zero vector if interpolation fails
                    return np.array([0.0, 0.0, 0.0])
                
                return np.array([u, v, 0.0])
            
            ## Define the colour function 
            def wind_color_func(pos:np.ndarray) -> float:
                x,y = pos[0], pos[1]
                ## Map froom screen coordinates to geographic coordinates
                lon = np.interp(x,[x_min,x_max],[lons.min(),lons.max()])
                lat = np.interp(y,[y_min,y_max],[lats.min(),lats.max()])

                #Interpolates
                u = u_interp([lat,lon])[0]
                v = v_interp([lat,lon])[0]

                # Calculate the magnitude
                return np.linalg.norm([u,v])
            
            
            # Calculate the range of the streamline to match the ImageObject
            x_range_min = round((img_width - img_width * CONFIG_STREAMPLOT['resize_factor']), 2) / 2
            y_range_min = round((img_height - img_height * CONFIG_STREAMPLOT['resize_factor']), 2) / 2
            
            ## Get min and max wind velocity
            min_wind_speed = VectorFieldConfig.DATASET['wind_speed'].values.min()
            max_wind_speed = VectorFieldConfig.DATASET['wind_speed'].values.max()
            
            ## Create the colorbar
            if VectorFieldConfig.CONFIG_COLORBAR['palette_array'] is not None:
                color_palette = ColorPalette(VectorFieldConfig.CONFIG_COLORBAR['palette_array'],
                                             data_min=min_wind_speed,
                                             data_max=max_wind_speed)
            else:
                ## this overwrite whatever pallette name passed 
                color_palette = ColorPalette(palette = VectorFieldConfig.CONFIG_COLORBAR['palette'],
                                             num_colors = VectorFieldConfig.CONFIG_COLORBAR['num_colors'],
                                             data_min=min_wind_speed,
                                             data_max=max_wind_speed)
            
            #save the colorbarplot
            color_palette.save_plot({'width_ratio':VectorFieldConfig.CONFIG_COLORBAR['width_ratio'],
                                     'title':VectorFieldConfig.CONFIG_COLORBAR['title'],
                                     'title_size':VectorFieldConfig.CONFIG_COLORBAR['title_size'],
                                     'label_size':VectorFieldConfig.CONFIG_COLORBAR['label_size'],
                                     'figsize':VectorFieldConfig.CONFIG_COLORBAR['figsize']
                                     }
                                    )
            
            ## Create a Manim palette colorspace for the  colorbar
            manim_color_palette = [ManimColor(hex_color) for hex_color in color_palette.get_hex_colors()]
            
            # Create stream lines
            stream_lines = StreamLines(
                wind_vector_func,
                x_range=[-1 * x_range_min, x_range_min, VectorFieldConfig.CONFIG_STREAMPLOT['delta_y']],
                y_range=[-1 * y_range_min, y_range_min, VectorFieldConfig.CONFIG_STREAMPLOT['delta_y']],
                color_scheme = wind_color_func,
                min_color_scheme_value = int(min_wind_speed),
                max_color_scheme_value = int(max_wind_speed),
                colors = manim_color_palette,
                dt= VectorFieldConfig.CONFIG_STREAMPLOT['dt'],
                padding=0,
                noise_factor=0.0,
                max_anchors_per_line= VectorFieldConfig.CONFIG_STREAMPLOT['max_anchors_per_line'],
                stroke_width= VectorFieldConfig.CONFIG_STREAMPLOT['stroke_width'],
                virtual_time= VectorFieldConfig.CONFIG_STREAMPLOT['virtual_time']
            )
            
            # Center the stream lines
            stream_lines.center()
            self.add(stream_lines)
            
            ## group
            vg_streamline = VGroup(geo_image,stream_lines)
            
            # Add title if specified
            title = None
            if VectorFieldConfig.CONFIG_TITLE['show_title']:
                title = Text(
                    VectorFieldConfig.CONFIG_TITLE['title_text'],
                    font_size=VectorFieldConfig.CONFIG_TITLE['title_font_size'],
                    color=VectorFieldConfig.CONFIG_TITLE['title_color']
                )
                #title.to_edge(UP)
                self.add(title.next_to(vg_streamline, UP, buff=0.02))
                
                
            # Add subtitle if specified
            if VectorFieldConfig.CONFIG_SUPTITLE['show_suptitle']:
                suptitle = Text(
                    VectorFieldConfig.CONFIG_SUPTITLE['suptitle_text'],
                    font_size=VectorFieldConfig.CONFIG_SUPTITLE['suptitle_font_size'],
                    color=VectorFieldConfig.CONFIG_SUPTITLE['suptitle_color']
                )
                if title is not None:
                    suptitle.next_to(title, DOWN, buff=0.5)
                else:
                    suptitle.to_edge(UP)
            
            ##Create a ImageObject for the colorbar
            colorbar_img = ImageMobject('colorbar.png')
            colorbar_img.height = vg_streamline.height
            self.add(colorbar_img.next_to(vg_streamline, RIGHT, buff=0.04))
            
            
            # Animate the stream lines
            stream_lines.start_animation(
                warm_up=False,
                flow_speed=VectorFieldConfig.CONFIG_STREAMPLOT['flow_speed'],
                time_width=VectorFieldConfig.CONFIG_STREAMPLOT['time_width']
            )
            
            self.wait(VectorFieldConfig.CONFIG_STREAMPLOT['animation_duration'])
            
            
    def _extract_wind_data(self):
        """Extract wind data from the global dataset"""
        dataset = VectorFieldConfig.DATASET
        u10 = dataset['u10'].values
        v10 = dataset['v10'].values
        lats = dataset['latitude'].values
        lons = dataset['longitude'].values
        
        return u10, v10, lats, lons
    
    def _create_interpolators(self, u10, v10, lats, lons):
        """Create interpolators for the wind components"""
        # Ensure lat is increasing and lon is increasing for interpolation
        if lats[0] > lats[-1]:
            lats = lats[::-1]
            u10 = u10[::-1, :]
            v10 = v10[::-1, :]
        if lons[0] > lons[-1]:
            lons = lons[::-1]
            u10 = u10[:, ::-1]
            v10 = v10[:, ::-1]
        
        # Create interpolators
        u_interp = RegularGridInterpolator((lats, lons), u10)
        v_interp = RegularGridInterpolator((lats, lons), v10)
        
        return u_interp, v_interp


class VectorFieldConfig:
    """
    Global configuration class for vector field animations.
    This allows the Scene class to access configuration parameters.
    """
    
    # Global variables to store dataset and image path
    DATASET = None
    BACKGROUND_IMAGE_PATH = None
    
    # Configuration dictionaries
    CONFIG_BASEPLOT = {
        'image_height': 7,
    }
    
    CONFIG_TITLE = {
        'show_title': False,
        'title_text': "ERA5 Wind - Vector Data",
        'title_font_size': 36,
        'title_color': WHITE,
    }
    
    CONFIG_SUPTITLE = {
        'show_suptitle': False,
        'suptitle_text': 'epsum leteris',
        'suptitle_font_size': 24,
        'suptitle_color': WHITE,
    }
    
    CONFIG_STREAMPLOT = {
        'delta_y': 0.15,
        'resize_factor': 0.04,
        'stroke_width': 1.0,
        'flow_speed': 2.0,
        'time_width': 0.3,
        'animation_duration': 4,
        'dt': 0.03,
        'max_anchors_per_line': 50,
        'color': WHITE,
        'virtual_time': 4,
    }
    
    CONFIG_COLORBAR = {
        'show': False,
        'palette_name': 'discrete1',
        'palette_array' : None,
        'num_colors' :4,
        'title': None,
        'title_size': 12,
        'label_size' : 16,
        'width_ratio' : 0.8,
        'figsize': (2,8)
    }
    
    @classmethod   
    def set_dataset(cls, dataset):
        """Set the global dataset"""
        cls.DATASET = dataset
        
    @classmethod
    def set_background_image_path(cls, image_path):
        """Set the global background image path"""
        cls.BACKGROUND_IMAGE_PATH = image_path
        
    @classmethod
    def configure_baseplot(cls, **kwargs):
        """Update baseplot configuration"""
        cls.CONFIG_BASEPLOT.update(kwargs)
        
    @classmethod
    def configure_title(cls, **kwargs):
        """Update title configuration"""
        cls.CONFIG_TITLE.update(kwargs)
        
    @classmethod
    def configure_suptitle(cls, **kwargs):
        """Update suptitle configuration"""
        cls.CONFIG_SUPTITLE.update(kwargs)
        
    @classmethod
    def configure_streamplot(cls, **kwargs):
        """Update streamplot configuration"""
        cls.CONFIG_STREAMPLOT.update(kwargs)
        
    @classmethod
    def configure_colorbar(cls, **kwargs):
        """Update streamplot configuration"""
        cls.CONFIG_COLORBAR.update(kwargs)
    
class VectorField_Animation:
    """
    A class that handles the creation of stream plots for wind data from ERA5 datasets
    
    This class creates dynamic visualizations by combining a background image with animated streamlines representing wind flow patterns. The streamlines are generated from ERA5 
    wind data and animated over the background image using Manim.
    
    The workflow involves:
    1. Loading a background image.
    2. Extracting wind data (u10, v10 components) from ERA5 dataset
    3. Creating interpolated wind vector fields
    4. Generating animated streamlines that flow over the background
    5. Rendering the final animation
    
    Configuration Options:
    ---------------------
    The class uses several configuration dictionaries to control different aspects:
    
    - **Main Config**: Output settings (file name, quality, dimensions)
    - **Base Plot Config**: Background image settings (height, positioning)
    - **Title Config**: Main title appearance and text
    - **Subtitle Config**: Secondary title with timestamp/metadata
    - **Streamplot Config**: Animation parameters (speed, colors, density)
    
    
    Parameters:
    -----------
    dataset : xarray.Dataset
        The ERA5 dataset containing wind data (u10, v10)
    background_image_path : str
        Path to the background image to use for the plot    
    """
    
    def __init__(self, dataset:xr.Dataset=None, background_image_path:str=None):
        """
        
         Initialize the VectorField_Animation with dataset and background image.
        
        Parameters:
        -----------
        dataset : xarray.Dataset
            ERA5 dataset containing wind components 'u10' and 'v10', along with 
            'latitude', 'longitude', and 'valid_time' coordinates. Can be set later 
            using set_dataset() method.
            
        background_image_path : str, optional
            Path to background image file (PNG, JPG, etc.) to use as map overlay.
            Can be set later using set_background_image() method.
            
        Configuration Parameters:
        ------------------------
        **Main Config**:
        - `output_file`: str (default 'wind_stream_plot')
            Name of the output file for the rendered animation.
        - `pixel_width, pixel_height`: int (default 854x480)
            Width of the output video in pixels. 
        - 'quaulity': str (default 'medium_quality')
            Quality of the rendered animation (options: 'low_quality', 'medium_quality', 'high_quality', 'fourk_quality').
            
        **Base Plot Config**:
        - `image_height`: float (default 7)
            Height of the baseplot image, in Manim units (default is 7). This height should be lesser than the height of the Manim canvas (by default 8).
        
        **Title Config**:
        - `show_title`: bool (default False)
            Whether to show the main title on the plot.
        - `title_text`: str (default "ERA5 Wind - Vector Data")
            Text for the main title.
        - `title_font_size`: int (default 36)
            Font size for the main title text.
        - `title_color`: str (default WHITE)
            Color of the main title text (default is WHITE).
            
        **Subtitle Config**:
        - `show_suptitle`: bool (default False)
            Whether to show the subtitle on the plot.
        - `suptitle_text`: str (default is the valid_time of the dataset)
            Text for the subtitle, typically a timestamp or metadata.
        - `suptitle_font_size`: int (default 24)
            Font size for the subtitle text.
        - `suptitle_color`: str (default WHITE)
            Color of the subtitle text (default is WHITE).
            
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
        
        
         Notes:
        ------
        - The class automatically handles coordinate transformations between 
          geographic (lat/lon) and screen coordinates
        - Streamlines are automatically sized to fit within the background image
        - Use configure() methods to adjust parameters after initialization
        
        """
        self.dataset = dataset
        self.background_image_path = background_image_path
        self.scene_class = None  
        self.temp_media_dir = None
        
        self.config_baseplot = {
            'image_height': 7,  # Height of the baseplot image in Manim units
        }
        
        self.config_title = {
            'show_title': False,  # Whether to show the title   
            'title_text': "ERA5 Wind - Vector Data",  # Title text
            'title_font_size': 36,  # Font size for the title
            'title_color': WHITE,  # Color of the title text
        }
        
        self.config_suptitle = {
            'show_suptitle': False,  # Whether to show the suptitle
            'suptitle_text': 'epsum leteris',  # Suptitle text  
            'suptitle_font_size': 24,  # Font size for the suptitle
            'suptitle_color': WHITE,  # Color of the suptitle text
        }
        
        self.config_streamplot = {
            'delta_y': 0.15,  # Linspace of the axis 
            'resize_factor': 0.05,  # Resize factor for the image
            'stroke_width': 1.0,  # Width of the stream lines
            'flow_speed': 2.0,  # Speed of the flow animation
            'time_width': 0.3,  # Width of the time window for the animation
            'animation_duration': 3,  # Duration of the animation in seconds
            'dt': 0.01,  # Time step for the animation
            'max_anchors_per_line': 100,  # Maximum number of anchors per stream line
            'color': WHITE,  # Color of the stream lines
            'virtual_time': 4,  # Virtual time for the animation
        }
        # Default configuration parameters
        self.config = {
            # Jupyter-specific options
            'output_file': 'wind_stream_plot',
            'pixel_width': 854,
            'pixel_height': 480,
            'preview_frames': 30,
            'transparent': False,
            'quality': 'medium_quality',  # low_quality, medium_quality, high_quality, fourk_quality
        }
        
        # Initialize the manim config for Jupyter compatibility
        self._setup_manim_config()
    
    def _setup_manim_config(self):
        """Configure Manim for Jupyter notebook compatibility"""
        # Store the original config
        self._original_config = {
            'preview': manim_config.preview,
            'output_file': manim_config.output_file,
            'pixel_width': manim_config.pixel_width,
            'pixel_height': manim_config.pixel_height,
            'transparent': manim_config.transparent,
        }
        
        # Set temp dir for media output
        self.temp_media_dir = tempfile.mkdtemp()
        manim_config.media_dir = self.temp_media_dir
    
    def configure(self, **kwargs):
        """
        Update configuration parameters.
        
        Parameters:
        -----------
        **kwargs : dict
            Configuration parameters to update
        
        Returns:
        --------
        self : StreamPlotHandler
            Returns self for method chaining
        """
        self.config.update(kwargs)
        
        # Update manim config based on new parameters
        if 'pixel_width' in kwargs:
            manim_config.pixel_width = self.config['pixel_width']
        if 'pixel_height' in kwargs:
            manim_config.pixel_height = self.config['pixel_height']
        if 'transparent' in kwargs:
            manim_config.transparent = self.config['transparent']
        if 'output_file' in kwargs:
            manim_config.output_file = self.config['output_file']
        if 'quality' in kwargs:
            manim_config.quality = self.config['quality']
            
        return self
    
    def configure_baseplot(self, **kwargs):
        """
        Update baseplot configuration parameters.
        
        Parameters:
        -----------
        **kwargs : dict
            Baseplot configuration parameters (e.g., image_height=6)
            
        Returns:
        --------
        self : VectorField_Animation
            Returns self for method chaining
        """
        self.config_baseplot.update(kwargs)
        return self
    
    def configure_title(self, **kwargs):
        """
        Update title configuration parameters.
        
        Parameters:
        -----------
        **kwargs : dict
            Title configuration parameters (e.g., show_title=True, title_text='My Title')
            
        Returns:
        --------
        self : VectorField_Animation
            Returns self for method chaining
        """
        self.config_title.update(kwargs)
        return self
    
    def configure_suptitle(self, **kwargs):
        """
        Update suptitle configuration parameters.
        
        Parameters:
        -----------
        **kwargs : dict
            Suptitle configuration parameters (e.g., show_suptitle=True, suptitle_text='Subtitle')
            
        Returns:
        --------
        self : VectorField_Animation
            Returns self for method chaining
        """
        self.config_suptitle.update(kwargs)
        return self
    
    def configure_streamplot(self, **kwargs):
        """
        Update streamplot configuration parameters.
        
        Parameters:
        -----------
        **kwargs : dict
            Streamplot configuration parameters (e.g., flow_speed=3.0, color='red')
            
        Returns:
        --------
        self : VectorField_Animation
            Returns self for method chaining
        """
        self.config_streamplot.update(kwargs)
        return self
    
    def get_config(self, section=None):
        """
        Get configuration parameters for a specific section or all sections.
        
        Parameters:
        -----------
        section : str, optional
            Configuration section to retrieve ('baseplot', 'title', 'suptitle', 'streamplot', 'main')
            If None, returns all configurations
            
        Returns:
        --------
        dict : Configuration parameters
        """
        if section == 'baseplot':
            return self.config_baseplot.copy()
        elif section == 'title':
            return self.config_title.copy()
        elif section == 'suptitle':
            return self.config_suptitle.copy()
        elif section == 'streamplot':
            return self.config_streamplot.copy()
        elif section == 'main':
            return self.config.copy()
        else:
            return {
                'main': self.config.copy(),
                'baseplot': self.config_baseplot.copy(),
                'title': self.config_title.copy(),
                'suptitle': self.config_suptitle.copy(),
                'streamplot': self.config_streamplot.copy()
            }
                     
    def create_manim_scene(self):
        """
        Create a Manim Scene class with the configured stream plot.
        
        Returns:
        --------
        Scene : manim.Scene
            A Manim Scene class with the configured stream plot
        """
        if self.dataset is None:
            raise ValueError("Dataset is required. Set it with set_dataset() method.")
        
        if self.background_image_path is None:
            raise ValueError("Background image path is required. Set it with set_background_image() method.")
        
        if self.config_suptitle['show_suptitle']:
            self.config_suptitle['suptitle_text'] = pd.to_datetime(str(self.dataset['valid_time'].values)).strftime('%Y-%m-%d %H:%M:%S')

        # Create a new Scene class dynamically
        class ConfiguredStreamPlot(Scene):
            def __init__(self_scene, **kwargs):
                super().__init__(**kwargs)
                self_scene.handler_ref = self  # Store reference to handler
            
            def construct(self_scene):
                # Load background image
                geo_image = ImageMobject(self.background_image_path)
                geo_image.height = self.config_baseplot['image_height']
                geo_image.center() # Center the image in the scene 
                
                ## Fade in the background image
                #self_scene.play(FadeIn(geo_image)) 
                
                # Add title if specified
                title = None
                if self.config_title['show_title']:
                    title = Text(self.config_title['title_text'],
                                       font_size=self.config_title['title_font_size'],
                                       color=self.config_title['title_color'])
                    title.to_edge(UP)
                    self_scene.add(title)
                    
                if self.config_suptitle['show_suptitle']:
                    suptitle = Text(self.config_suptitle['suptitle_text'],
                                       font_size=self.config_suptitle['suptitle_font_size'],
                                       color=self.config_suptitle['suptitle_color'])
                    if title is not None:
                        suptitle.next_to(title,DOWN, buff=0.5)
                    else:
                        suptitle.to_edge(UP)
                    self_scene.add(suptitle)
                
                # Extract dimensions from ImageMobject
                img_width = geo_image.width
                img_height = geo_image.height
                x_min, x_max = geo_image.get_left()[0], geo_image.get_right()[0]
                y_min, y_max = geo_image.get_bottom()[1], geo_image.get_top()[1]
                
                # Extract wind data
                u10, v10, lats, lons = self._extract_wind_data()
                
                # Create interpolators
                u_interp, v_interp = self._create_interpolators(u10, v10, lats, lons)
                
                # Define wind vector function for the stream lines
                def wind_vector_func(pos):
                    x, y = pos[0], pos[1]
                    # Map from screen coordinates to geographic coordinates
                    lon = np.interp(x, [x_min, x_max], [lons.min(), lons.max()])
                    lat = np.interp(y, [y_min, y_max], [lats.min(), lats.max()])
                    
                    # Use interpolator
                    try:
                        u = u_interp([lat, lon])[0]
                        v = v_interp([lat, lon])[0]
                    except:
                        # Return zero vector if interpolation fails
                        return np.array([0.0, 0.0, 0.0])
                    
                    return np.array([u, v, 0.0])
                
                # Calculate the range of the streamline to match the ImageObject
                x_range_min = round((img_width - img_width * self.config_streamplot['resize_factor']), 2) / 2
                y_range_min = round((img_height - img_height * self.config_streamplot['resize_factor']), 2) / 2
                
                ## Set spacement between axis ticks 
                delta_y = self.config_streamplot['delta_y']
                
                # Create stream lines
                stream_lines = StreamLines(
                    wind_vector_func, ## the function to compute the wind vector at a given position
                    x_range=[-1 * x_range_min, x_range_min, delta_y],
                    y_range=[-1 * y_range_min, y_range_min, delta_y],
                    color=self.config_streamplot['color'],
                    dt=self.config_streamplot['dt'],
                    padding=0,
                    noise_factor=0.0,
                    max_anchors_per_line=self.config_streamplot['max_anchors_per_line'],
                    stroke_width=self.config_streamplot['stroke_width'],
                    virtual_time=self.config_streamplot['virtual_time']
                )
                
                # Center the stream lines
                stream_lines.center()
                self_scene.add(stream_lines)
                
                # Animate the stream lines
                stream_lines.start_animation(
                    warm_up=False,
                    flow_speed=self.config_streamplot['flow_speed'],
                    time_width=self.config_streamplot['time_width']
                )
                
                self_scene.wait(self.config_streamplot['animation_duration'])
        
        self.scene_class = ConfiguredStreamPlot
        return ConfiguredStreamPlot
    
    def _extract_wind_data(self):
        """
        Extract wind data (u10, v10) and coordinates (lats, lons) from the dataset.
        
        Returns:
        --------
        tuple : (u10, v10, lats, lons)
            The wind components and coordinate arrays
        """
        u10 = self.dataset['u10'].values
        v10 = self.dataset['v10'].values
        lats = self.dataset['latitude'].values
        lons = self.dataset['longitude'].values
        
        return u10, v10, lats, lons
    
    def _create_interpolators(self, u10, v10, lats, lons):
        """
        Create interpolators for the wind components.
        
        Parameters:
        -----------
        u10 : numpy.ndarray
            The u-component of wind
        v10 : numpy.ndarray
            The v-component of wind
        lats : numpy.ndarray
            The latitude coordinates
        lons : numpy.ndarray
            The longitude coordinates
        
        Returns:
        --------
        tuple : (u_interp, v_interp)
            The interpolators for u and v components
        """
        # Ensure lat is increasing and lon is increasing for interpolation
        if lats[0] > lats[-1]:
            lats = lats[::-1]
            u10 = u10[::-1, :]
            v10 = v10[::-1, :]
        if lons[0] > lons[-1]:
            lons = lons[::-1]
            u10 = u10[:, ::-1]
            v10 = v10[:, ::-1]
        
        # Create interpolators
        u_interp = RegularGridInterpolator((lats, lons), u10)
        v_interp = RegularGridInterpolator((lats, lons), v10)
        
        return u_interp, v_interp
    
    def set_dataset(self, dataset):
        """
        Set the dataset for the stream plot.
        
        Parameters:
        -----------
        dataset : xarray.Dataset
            The ERA5 dataset containing wind data (u10, v10)
        
        Returns:
        --------
        self : StreamPlotHandler
            Returns self for method chaining
        """
        self.dataset = dataset
        return self
    
    def set_background_image(self, image_path):
        """
        Set the background image path for the stream plot.
        
        Parameters:
        -----------
        image_path : str
            Path to the background image file
        
        Returns:
        --------
        self : StreamPlotHandler
            Returns self for method chaining
        """
        self.background_image_path = image_path
        return self
    
    def render_to_notebook(self, display_mode='video'):
        """
        Render the animation and display it directly in the notebook.
        
        Parameters:
        -----------
        display_mode : str
            How to display the animation - 'video' or 'html'
            
        Returns:
        --------
        None : Displays the animation in the notebook
        """
        if self.scene_class is None:
            self.scene_class = self.create_manim_scene()
        
        # Configure manim for notebook display
        manim_config.output_file = self.config['output_file']
        manim_config.preview = True
        
        # Render the scene
        scene = self.scene_class()
        scene.render()
        
        # Get the path to the video file
        media_dir = manim_config.get_dir("media_dir")
        quality = self.config['quality']
        video_dir = os.path.join(media_dir, "videos", self.scene_class.__name__, quality)
        video_path = os.path.join(video_dir, f"{self.config['output_file']}.mp4")
        
        if display_mode == 'video':
            return display(Video(video_path, embed=True, html_attributes="controls autoplay loop"))
        elif display_mode == 'html':
            video_tag = f"""
            <video width="{self.config['pixel_width']}" height="{self.config['pixel_height']}" controls autoplay loop>
                <source src="{video_path}" type="video/mp4">
                Your browser does not support the video tag.
            </video>
            """
            return display(HTML(video_tag))
        else:
            print(f"Animation rendered to: {video_path}")
    
    def preview(self, frame_number=0):
        """
        Generate a preview frame of the animation without rendering the full animation.
        
        Parameters:
        -----------
        frame_number : int
            The frame number to preview
            
        Returns:
        --------
        None : Displays a preview image in the notebook
        """
        from manim import config as manim_cfg
        from manim import tempconfig
        
        if self.scene_class is None:
            self.scene_class = self.create_manim_scene()
        
        # Use tempconfig to temporarily modify the config
        with tempconfig({"save_last_frame": True, "output_file": f"{self.config['output_file']}_preview"}):
            scene = self.scene_class()
            scene.render()
            
            # Get the path to the image file
            media_dir = manim_cfg.get_dir("media_dir")
            quality = self.config['quality']
            images_dir = os.path.join(media_dir, "images", self.scene_class.__name__)
            image_path = os.path.join(images_dir, f"{self.config['output_file']}_preview.png")
            
            # Display the image
            from IPython.display import Image
            return display(Image(image_path))
    
    def _cleanup(self):
        """Clean up temporary files if needed"""
        import shutil
        if self.temp_media_dir and os.path.exists(self.temp_media_dir):
            shutil.rmtree(self.temp_media_dir)
            
    def __del__(self):
        """Destructor to clean up resources"""
        self._cleanup()


