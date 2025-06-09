# Lombric Quiver

A  Python library develop for end-to-end geospatial animations. 
Using a seamless integration with [Earth Data Hub](https://platform.destine.eu/services/service/earth-data-hub/) and [Destine Earth](https://platform.destine.eu/services/service/earth-data-hub/) that Lombric Quiver library allows users to retrieve, pre-process and create animations with one tool. 

The library uses as an engine the Manim community, an open-source projected developt by [3blue1brown](https://www.youtube.com/c/3blue1brown) Youtube channel to create mathematics and physics animations. Manim is an animator engine, that uses practices of Orientation Object Programing to create stunning animations. 

##  Main Classes
* `ERA5_Procesor` - Retrieve and Pre-process geospatial data from ERA5.
* `Colormap` - Allow palette generation .
* `VectorFieldAnimation` - Creates the Scene and animate stream lines.
* `Base plot` - Deals with background plots that belongs to the scene.

## Project layout

    mkdocs.yml    # The configuration file.
    docs/
        index.md  # The documentation homepage.
        ...       # Other markdown pages, images and other files.
