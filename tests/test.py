# -*- coding: utf-8 -*-

""" This module contains tests for the lombricquiver package.
It includes tests for the VectorFieldAnimation class and the ERA5DataProcessor class.       
It also includes tests for the configuration of the animation parameters and the generation of the quiver plot.

"""
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import xarray as xr
import pytest
import numpy as np
import pytest
from pathlib import Path
from lombricquiver.base_map import create_layer_base
from lombricquiver.era5_processor import ERA5DataProcessor
from lombricquiver.manim_vector_field import (
    VectorFieldAnimation,
    VectorFieldConfig,
    BasePlotConfig,
    TitleConfig,
    SubtitleConfig,
    StreamPlotConfig,
    ColorbarConfig,
)
@pytest.fixture
def example_dataset():
    """Fixture to provide an example dataset for testing."""
    import xarray as xr
    return xr.open_dataset("docs/examples/dataset/era5_data.nc")

@pytest.fixture
def processor(example_dataset):
    """Fixture to create an instance of ERA5DataProcessor."""
    return ERA5DataProcessor(
        ds=example_dataset,
        variables=['u10', 'v10', 't2m'],
        date_range=["2023-03-05", "2023-03-05"],
        spatial_range={
            "lat": [30, 50],
            "lon": [-20, 20]
        }
    )

@pytest.fixture
def test_image():
    """Fixture to provide a test image path."""
    return Path("docs/img/base_layer.png")

def test_era5_data_processor(processor):
    """Test the ERA5DataProcessor instance."""
    assert processor.dataset is not None
    assert 'u10' in processor.variables
    assert 'v10' in processor.variables
    assert 't2m' in processor.variables
    assert processor.date_range == ["2023-03-05", "2023-03-05"]
    assert processor.spatial_range['lat'] == [30, 50]
    assert processor.spatial_range['lon'] == [-20, 20]

def test_vectorfield_config_background(example_dataset):
    config = VectorFieldConfig()
    config.background_image_path = "docs/img/base_layer.png"
    print(config.background_image_path)
    assert config.background_image_path is not None
    
def test_vectorfield_config_is_ready(example_dataset, test_image):
    config = VectorFieldConfig()
    config.dataset = example_dataset
    config.background_image_path = test_image
    assert config.is_ready() == True

def test_vectorfieldanimation_setters(example_dataset,test_image):
    vfa=VectorFieldAnimation()
    vfa.set_dataset(example_dataset)
    vfa.set_background_image(test_image)
    assert vfa.dataset() is not None
    assert vfa.config.background_image_path == test_image


def test_vectorfieldanimation_configure_methods(example_dataset, test_image):
    vfa = VectorFieldAnimation()
    vfa.set_dataset(example_dataset)
    vfa.set_background_image(test_image)
    vfa.configure_title(show_title=True, title_text="Test Title")
    vfa.configure_subtitle(show_suptitle=True, suptitle_text="Test Subtitle")
    vfa.configure_streamplot(flow_speed=3.0)
    vfa.configure_colorbar(show=True, palette="viridis", num_colors=5)
    assert vfa.config.title.show_title is True
    assert vfa.config.title.title_text == "Test Title"
    assert vfa.config.subtitle.show_suptitle is True
    assert vfa.config.subtitle.suptitle_text == "Test Subtitle"
    assert vfa.config.streamplot.flow_speed == 3.0
    assert vfa.config.colorbar.show is True
    assert vfa.config.colorbar.palette == "viridis"
    assert vfa.config.colorbar.num_colors == 5


def test_vectorfieldanimation_is_ready(example_dataset, test_image):
    vfa = VectorFieldAnimation()
    vfa.set_dataset(example_dataset)
    vfa.set_background_image(test_image)
    assert vfa.is_ready()
    assert vfa.get_missing_requirements() == []


def test_vectorfieldanimation_scene_class(example_dataset, test_image):
    vfa = VectorFieldAnimation()
    vfa.set_dataset(example_dataset)
    vfa.set_background_image(test_image)
    scene_class = vfa.get_scene_class()
    assert callable(scene_class)
    
### Testing the creation of the image 
### Testing the creation of the image 
@pytest.fixture
def dict_extract_var():
    # Minimal valid input dictionary
    return {
        "long": np.linspace(-10, 10, 5),
        "lat": np.linspace(35, 45, 5),
        "wind_speed": np.random.rand(5, 5)
    }
    
def test_create_layer_base_creates_file(tmp_path, dict_extract_var):
    file_name = tmp_path / "test_base_layer.png"
    result = create_layer_base(
        dict_extract_var,
        var_heatmap="wind_speed",
        file_name=str(file_name),
        dpi=50,  # lower dpi for faster test
        height_inches=2
    )
    assert os.path.exists(result)
    assert result == str(file_name)

def test_missing_long_lat_raises(dict_extract_var):
    d = dict_extract_var.copy()
    d.pop("long")
    with pytest.raises(ValueError):
        create_layer_base(d)

def test_missing_var_heatmap_raises(dict_extract_var):
    d = dict_extract_var.copy()
    d.pop("wind_speed")
    with pytest.raises(ValueError):
        create_layer_base(d, var_heatmap="wind_speed")

def test_stream_lines_requires_dataset(dict_extract_var):
    # Should raise if stream_lines is True but dataset_subsampled is None
    with pytest.raises(ValueError):
        create_layer_base(dict_extract_var, stream_lines=True)


def test_stream_lines_requires_vars(dict_extract_var):
    # Should raise if required vars are missing in dataset_subsampled
    ds = xr.Dataset({"foo": (("x",), [1, 2, 3])})
    with pytest.raises(ValueError):
        create_layer_base(dict_extract_var, stream_lines=True, dataset_subsampled=ds)