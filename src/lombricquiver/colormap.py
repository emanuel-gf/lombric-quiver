import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.gridspec as gridspec

class ColorPalette:
    """
    A class to handle matplotlib color palettes and custom hex color arrays.
    
    Attributes:
        palette: matplotlib colormap, palette name, or list of hex colors
        num_colors: number of colors to extract from the palette
        data_min: minimum data value
        data_max: maximum data value
        is_custom: whether the palette is a custom hex color array
    """
    
    def __init__(self, palette, num_colors=None, data_min=None, data_max=None):
        """
        Initialize the ColorPalette class.
        
        Parameters:
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
            Maximum data value. If None, defaults to num_colors
        """
        self.palette = palette
        self.is_custom = isinstance(palette, (list, tuple, np.ndarray))
        
        if self.is_custom:
            self._validate_hex_colors(palette)
            self.num_colors = len(palette) if num_colors is None else num_colors
            self._custom_colors = list(palette)
        else:
            if num_colors is None:
                raise ValueError("num_colors must be specified for matplotlib palettes")
            self.num_colors = num_colors
            
        self.data_min = data_min if data_min is not None else 0
        self.data_max = data_max if data_max is not None else self.num_colors
        self._colormap = self._get_colormap()
        
    def _validate_hex_colors(self, colors):
        """Validate that all colors in the list are valid hex colors."""
        for i, color in enumerate(colors):
            try:
                mcolors.to_rgba(color)
            except ValueError:
                raise ValueError(f"Invalid color at index {i}: '{color}'. "
                               f"Please provide valid hex colors (e.g., '#FF5733', '#3366CC')")
    
    def _get_colormap(self):
        """Get the matplotlib colormap object."""
        if self.is_custom:
            return mcolors.ListedColormap(self._custom_colors)
        elif isinstance(self.palette, str):
            try:
                return plt.get_cmap(self.palette)
            except ValueError:
                raise ValueError(f"Unknown colormap name: {self.palette}")
        else:
            return self.palette
    
    def get_hex_colors(self):
        """
        Extract hex colors from the palette.
        
        Returns:
        --------
        list: Array of hex color strings with length num_colors
        """
        if self.is_custom:
            # If we need more colors than provided, interpolate
            if self.num_colors <= len(self._custom_colors):
                # Sample from the existing colors
                indices = np.linspace(0, len(self._custom_colors) - 1, self.num_colors)
                indices = np.round(indices).astype(int)
                return [self._custom_colors[i] for i in indices]
            else:
                # Interpolate to get more colors
                color_indices = np.linspace(0, 1, self.num_colors)
                colors_rgba = self._colormap(color_indices)
                hex_colors = []
                for rgba in colors_rgba:
                    rgb = rgba[:3]
                    hex_color = mcolors.to_hex(rgb)
                    hex_colors.append(hex_color)
                return hex_colors
        else:
            # Create linspace from 0 to 1 with num_colors points
            color_indices = np.linspace(0, 1, self.num_colors)
            
            # Sample colors from the colormap
            colors_rgba = self._colormap(color_indices)
            
            # Convert RGBA to hex
            hex_colors = []
            for rgba in colors_rgba:
                rgb = rgba[:3]
                hex_color = mcolors.to_hex(rgb)
                hex_colors.append(hex_color)
            
            return hex_colors
    
    def get_color_for_value(self, value):
        """
        Get the hex color corresponding to a specific data value.
        
        Parameters:
        -----------
        value : float
            The data value to map to a color
            
        Returns:
        --------
        str: Hex color string corresponding to the value
        """
        # Normalize the value to [0, 1] range
        if self.data_max == self.data_min:
            normalized_value = 0.5
        else:
            normalized_value = (value - self.data_min) / (self.data_max - self.data_min)
        
        # Clamp to [0, 1] range
        normalized_value = max(0, min(1, normalized_value))
        
        # Get color from colormap
        rgba = self._colormap(normalized_value)
        return mcolors.to_hex(rgba[:3])
    
    def plot_palette(self, figsize=None, title=None,
                     title_size=12, label_size=16,
                     width_ratio=0.8):
        """
        Create a colorbar visualization of the palette with data range axis.
        
        Parameters:
        -----------
        figsize : tuple, optional
            Figure size (width, height). Auto-calculated if None
        title : str, optional
            Title for the plot. If None, uses palette name or 'Custom Palette'
        title_size : int, optional
            Title font size
        label_size : int, optional
            Font size for the colorbar label. Default is 16
        width_ratio : float
            The width ratio of the colorbar. Bigger size implies thinner colorbar
            
        Returns:
        --------
        matplotlib.figure.Figure: The created figure object
        """
        
        if figsize is None:
            figsize = (2, 8)
    
        fig = plt.figure(figsize=figsize)

        width_ratio_aux = (1-width_ratio)/2
        
        # left and right columns are spacers
        gs = gridspec.GridSpec(1, 3, width_ratios=[width_ratio_aux, width_ratio, width_ratio_aux]) 
        cax = fig.add_subplot(gs[1])
    
        norm = mcolors.Normalize(vmin=self.data_min, vmax=self.data_max)
        scalar_mappable = plt.cm.ScalarMappable(norm=norm, cmap=self._colormap)
    
        cbar = fig.colorbar(scalar_mappable,
                            cax=cax,
                            orientation='vertical',
                            extend='both')
    
        # Set default title if none provided
        if title is None:
            title = 'm/s'
    
        cbar.set_label(title, fontsize=title_size)
        cbar.ax.tick_params(labelsize=label_size)
    
        return fig
        

    def save_plot(self, filename='colorbar', dpi=300, bbox_inches='tight', **kwargs):
        """
        Create and save a colorbar visualization of the palette.
        
        Parameters:
        -----------
        filename : str
            Output filename (e.g., 'palette.png', 'colorbar.pdf')
        dpi : int, optional
            Resolution for output image. Default is 300
        bbox_inches : str, optional
            Bounding box in inches. Default is 'tight'
        **kwargs: Any arg regarding the plot_palette method of the class. 
        """
        fig = self.plot_palette(**kwargs)
        fig.savefig(filename, dpi=dpi, bbox_inches=bbox_inches)
        plt.close(fig)  
        print(f"Colorbar saved as the following file_name: {filename}")
    
    def __repr__(self):
        """String representation of the ColorPalette object."""
        if self.is_custom:
            return f"ColorPalette(custom_colors={len(self._custom_colors)} colors, num_colors={self.num_colors}, data_range=[{self.data_min}, {self.data_max}])"
        else:
            return f"ColorPalette(palette='{self.palette}', num_colors={self.num_colors}, data_range=[{self.data_min}, {self.data_max}])"


