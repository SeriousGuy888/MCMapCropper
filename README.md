# MCMapCropper


- [MCMapCropper](#mcmapcropper)
  - [Purpose](#purpose)
    - [Use Case](#use-case)
  - [How to Use](#how-to-use)
  - [Examples](#examples)


## Purpose
I made this project because in order to automatically crop many **exported minimap images** ([from the Minecraft mod Xaero's World Map](https://www.curseforge.com/minecraft/mc-mods/xaeros-world-map)) to the same location.

The input files **don't have to have the same dimensions** ― minimap exports from different days may get progressively bigger in dimensions as you explore more of the world, and **the same location may appear at different pixel coordinates in different images**. This project is made to automatically get around that.

### Use Case
You might find this project useful if you
- a set of map images across many different days like in `/example_input/` in this repo.
- a need to crop these maps to get a sequence of images of a certain location in the maps across many different days (eg: for a timelapse). An example of what this project outputs can be found in `/example_output/`.

## How to Use

1. Install the pip requirements:
   ```bash
   pip install -r requirements.txt
   ```
2. Add images and appropriate data into `input` folder.
   - Place a set of map images (`.png`) in `/input/maps/`.

   - Run `/tools/align_images_to_coords.py` to create an `/input/origin_offsets.json` file which stores where x=0, z=0 in game would be depicted on each of the maps.
   \
   \
   You will be prompted to enter where `0, 0` is on the first image. If you are using the example data, enter `x=512, y=0`. This may be different for your own data.
   \
   \
   This allows all the maps to be aligned on the same grid and also allows for **easy conversion** between *Minecraft in game coordinates* & *image pixel coordinates* later.
   \
   \
   <sub>
   [Template Matching with Python OpenCV](https://docs.opencv.org/5.x/d4/dc6/tutorial_py_template_matching.html) is used to automatically find how the original image has shifted compared to later images. I don't know if this is an efficient way to do this, but it does seem to work pretty reliably ¯\\\_(ツ)\_/¯
   </sub>

   - Run `/tools/create_crop_preset.py` to select a rectangular area for the program to crop to. The script then converts your input (in pixel coords) to Minecraft coords (using the output from the previous step) and generates a preset that you can copy and paste into `/input/origin_offsets.json`.
     - This script will try to open Paint.NET from the default installation location on Windows. You could change this if you don't have it installed or want to find the selection box locations yourself.
   
   - Alternatively, you can open up the earliest map image and crop some part of the image that you want to crop all the images to. Then, save this to `input/crops/templates`.
3. Run `main.py`. You will get the following output:
   ```console
   $ python main.py

   Do you want to
   [1] use the JSON file with preset Minecraft coordinates (more reliable), or
   [2] use an image template to crop to (will use template matching to find where the image is the map)?
   ```
   
   - Select **Option 1** if you want to use the preset JSON file (eg: created using `/tools/create_crop_preset.py`).
     - Select preset to use if prompted.
   - Select **Option 2** if you want to use an image template (eg: a piece of the first map image). This will use template matching to find where the image is the map. It will not work if the image is not present in the first map.
     - Select template file to use if prompted.
   - Output images should appear in `/output/`.

## Examples
Sample files can be found in this repo in `/example_input/` and `/example_output/`.

You can run the `main.py` script on the example input files by renaming `/example_input/` to `/input/` and running `python main.py`.