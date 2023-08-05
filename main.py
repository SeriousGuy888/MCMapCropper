"""
Using the images in the `MAP_DIR` directory, crop each image to the same area.

This script can either
- use a template image to crop to (using template matching to find where the
  image is the map), or
- use a JSON file with preset Minecraft coordinates to crop to (more reliable).

Template images are just some part of one of the maps cropped to an area and
saved as an image. The program will do its best to find where that image is in
each map image, and crop to that area.

The JSON file with preset Minecraft coordinates should contain cropping presets
that specify a rectangle in Minecraft coordinates. The program will convert
those coordinates to pixel coordinates and crop to that area.
- The `tools/create_crop_preset.py` script can be used to create these presets.

The MC-coordinate to pixel-coordinate conversion is done using the offsets in
the `ORIGIN_OFFSETS_PATH` file.
- That file can be created using the `tools/align_images_to_coords.py` script.
"""

from dataclasses import dataclass
import json
import os
import cv2 as cv
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from tqdm import tqdm

from utils.match_template import match_template

INPUT_DIR = "./input/"
OUTPUT_DIR = "./output/"

MAP_DIR = INPUT_DIR + "maps/"

CROPS_DIR = INPUT_DIR + "crops/"
TEMPLATE_DIR = CROPS_DIR + "templates/"
DEFAULT_TEMPLATE_NAME = ""  # Leave empty to prompt user to specify
UNDERLAYS_DIR = INPUT_DIR + "underlays/"

##################################################
CROP_PRESETS = CROPS_DIR + "presets.json"
"""
This is a path to a JSON file with an array of cropping presets.

The presets are specified as rectangles in Minecraft coordinates, which allows
each image to be cropped to the same area even when the images are of different
dimensions.

These cropping templates are structured like this:
```
{
  "title": "Template title",
  "description": "Template description",
  "rect": [x1, y1, x2, y2]  // These are **Minecraft in-game coordinates**, not
                            // pixel coordinates. The coordinates the images are
                            // aligned to are determined in `CENTERS_FILE_PATH`
}
```

This script will, after a user selects a preset, convert the Minecraft coords to
pixel coordinates and crop the image to that area.
"""
##################################################

##################################################
ORIGIN_OFFSETS_PATH = INPUT_DIR + "origin_offsets.json"
"""
This is a path to a file with the pixel coordinates of where zero-zero is (or
would be) on each map image. These coordinates act as an offset for each image,
allowing pixel coordinates to be converted to what Minecraft coordinates in game
that that pixel depicts (or vice versa).

This file is structured like this:
```
{
  "image_name.png": [x, y],
  ...
}
```

- image_name.png is the name of the image file in the `MAP_DIR` directory.
- [x, y] represents a pixel coordinate in the image.
  - That pixel coordinate is zero-zero in Minecraft coordinates.
"""
##################################################

FONT = ImageFont.truetype("./fonts/UbuntuMono-Regular.ttf", 24)

# if True, we will add the image name each was cropped from to the top of the
# output image
ENABLE_INFO_ON_IMAGE = False


@dataclass
class CropPreset:
  rect: tuple[int, int, int, int]
  underlay: str | None


def main():
  template = prompt_for_template()
  center_offsets = get_center_offsets()

  # stop if not all the filenames are present in the centers file
  if len(center_offsets) != len(os.listdir(MAP_DIR)):
    raise ValueError(
        "Not all map images have a center offset in the centers file.")

  first_crop_rect, first_offset, underlay_path = None, None, None

  if type(template) is CropPreset:
    first_crop_rect = template.rect
    underlay_path = template.underlay
    first_offset = (0, 0)
  else:
    first_crop_rect, first_offset = get_first_position(template)

  underlay = None
  if underlay_path:
    underlay = Image.open(underlay_path)  # Open the underlay image

    # Scale the underlay image to the size of the output rectangle
    top_left, bottom_right = first_crop_rect
    underlay = underlay.resize((bottom_right[0] - top_left[0],
                                bottom_right[1] - top_left[1]),
                               Image.NEAREST)

    # add a transluscent black overlay to the underlay image
    underlay = Image.alpha_composite(underlay.convert("RGBA"),
                                     Image.new("RGBA",
                                               underlay.size,
                                               (0, 0, 0, 200)))

  files = tqdm(os.listdir(MAP_DIR), unit="images")
  for file_name in files:
    if not file_name.endswith(".png"):
      continue

    files.set_description(f"Cropping {file_name}...")

    # the zero-zero offset of the current image
    curr_offset = center_offsets[file_name]
    net_offset = (  # the offset of this image relative to the first image
        curr_offset[0] - first_offset[0],
        curr_offset[1] - first_offset[1]
    )

    img_path = MAP_DIR + file_name

    top_left, bottom_right = first_crop_rect

    top_left = (top_left[0] + net_offset[0],
                top_left[1] + net_offset[1])
    bottom_right = (bottom_right[0] + net_offset[0],
                    bottom_right[1] + net_offset[1])

    img = Image.open(img_path)

    img = crop_img(img, top_left, bottom_right)

    # If an underlay image was specified, put it under the cropped image
    if underlay:
      img = add_underlay(img, underlay)

    if ENABLE_INFO_ON_IMAGE:
      img = add_img_info(img, file_name)

    if not os.path.exists(OUTPUT_DIR):
      os.mkdir(OUTPUT_DIR)
    output_path = OUTPUT_DIR + file_name
    img.save(output_path)

  print("Done!")


def add_underlay(img: Image, underlay: Image) -> Image:
  """
  Given the original image and an underlay image, combine the two by placing
  the underlay image underneath the original image, such that any transparent
  pixels would show the underlay image.
  """

  # remove black pixels from the original image
  img = make_black_transparent(img)

  # only add the underlay image if the original image has any transparent
  # pixels through which the underlay image would be visible.
  if img.getchannel("A").getbbox():  # if image has any transparent pixels
    # add the original image on top of the underlay image
    # https://www.geeksforgeeks.org/python-pil-image-alpha_composite-method/
    img = Image.alpha_composite(underlay.convert("RGBA"), img)
  
  return img


def make_black_transparent(img: Image) -> Image:
  """
  Given an image, take each pixel, and if it is #000000, make it transparent.
  https://stackoverflow.com/a/71859851
  """

  imga = img.convert("RGBA")  # n x m x 4

  imga = np.asarray(imga)
  r, g, b, a = np.rollaxis(imga, axis=-1)  # split into 4 n x m arrays
  r_m = r != 0  # binary mask for red channel, True for all non black values
  g_m = g != 0  # binary mask for green channel, True for all non black values
  b_m = b != 0  # binary mask for blue channel, True for all non black values

  # combine the three masks using the binary "or" operation
  # this results in a mask that is True for any pixel that is not black
  not_black_m = ((r_m == 1) | (g_m == 1) | (b_m == 1))

  # multiply the combined binary mask with the alpha channel
  a = a * not_black_m

  # stack the img back together
  imga = Image.fromarray(np.dstack([r, g, b, a]), "RGBA")

  return imga


def get_first_position(template: cv.Mat) -> tuple[tuple[tuple[int, int],
                                                        tuple[int, int]],
                                                  tuple[int, int]]:
  """
  Take the first image in the `MAP_DIR` directory, then find the position of the
  template in that image.

  Returns
  ```
  tuple(
    "the rectangle that the template match occupies",
    "the image's origin offset"
  )
  ```
  """

  first_img_name = os.listdir(MAP_DIR)[0]
  if not first_img_name.endswith(".png"):
    raise FileNotFoundError(
        f"First image `{first_img_name}` is not a PNG file.")

  crop_rectangle = match_template(MAP_DIR + first_img_name, template)
  zero_zero_offset = get_center_offsets()[first_img_name]

  return (crop_rectangle, zero_zero_offset)


def get_center_offsets() -> dict[str, tuple[int, int]]:
  """
  Get the dictionary of each image's center coordinates.
  """

  if not os.path.exists(ORIGIN_OFFSETS_PATH):
    raise FileNotFoundError(f"Centers file `{ORIGIN_OFFSETS_PATH}` not found.")

  with open(ORIGIN_OFFSETS_PATH, "r") as f:
    return json.loads(f.read())


def prompt_for_template() -> cv.Mat | CropPreset:
  """
  If the default template name exists, read that as the template.
  Otherwise, prompt the user to choose one of the files from the folder.
  """

  # ask user if they want to use an image template or use the json file
  # with minecraft coordinates

  should_use_img_templates = 1 == prompt_select_from_list(
      message="Do you want to",
      options=[
          "use the JSON file with preset Minecraft coordinates (more reliable), or",
          "use an image template to crop to (will use template matching to find where the image is the map)?"
      ])

  if should_use_img_templates:
    template_name = DEFAULT_TEMPLATE_NAME

    if not template_name:
      file_list = os.listdir(TEMPLATE_DIR)
      template_idx = prompt_select_from_list(
          file_list, "Select template image to crop to: ")
      template_name = file_list[template_idx]

    template_path = TEMPLATE_DIR + template_name

    if not os.path.exists(template_path):
      raise FileNotFoundError(f"Template file `{template_path}` not found.")
    return cv.imread(template_path, 0)
  else:
    # read the json file with cropping templates

    if not os.path.exists(CROP_PRESETS):
      raise FileNotFoundError(
          f"Template file `{CROP_PRESETS}` not found.")

    templates_data = None
    with open(CROP_PRESETS, "r") as f:
      templates_data = json.loads(f.read())

    options = [
        f"""  {x['title']} - {x['rect']}
          {x['description']}
""" for x in templates_data]

    template_idx = prompt_select_from_list(options, "Select crop template: ")
    x1, y1, x2, y2 = templates_data[template_idx]["rect"]

    rect = ((x1, y1), (x2, y2))

    underlay = None
    try:
      underlay = UNDERLAYS_DIR + templates_data[template_idx]["underlay"]
    except KeyError:
      pass

    return CropPreset(
        rect=rect,
        underlay=underlay
    )


def prompt_select_from_list(options: list[str], message: str = "Select:") -> int:
  """
  Given a list of options, prompt the user to select one of them.
  This will return the **index** of the selected option.
  """

  if not options:
    raise ValueError("No options provided.")

  inp = ""
  prompt_msg = f"\n\n{message}\n"

  for index, item in enumerate(options):
    prompt_msg += f"[{index+1}] {item}\n"
  prompt_msg += "\nInput selection number: "

  while inp.lower() not in map(str, range(1, len(options) + 1)):
    inp = input(prompt_msg)
  selection_idx = int(inp) - 1
  print("\n")

  return selection_idx


def add_img_info(img: Image, info_text: str, section_height: int = 35) -> Image:
  """
  Add a section at the top of the image with space to add some extra text.
  """

  dimensions = (img.width, img.height + section_height)
  new_img = Image.new("RGBA", dimensions, "black")
  new_img.paste(img, (0, section_height))

  d = ImageDraw.Draw(new_img)
  d.text((10, 5), info_text, font=FONT, fill="lightgray")

  return new_img


def crop_img(img: Image,
             top_left: tuple[int, int],
             bottom_right: tuple[int, int]) -> Image:
  crop_rect = (top_left[0], top_left[1], bottom_right[0], bottom_right[1])
  return img.crop(crop_rect)


if __name__ == "__main__":
  main()
