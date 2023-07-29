"""
This tool is used to align all the images in the `maps/` directory to the
same Minecraft coordinate grid.

This is done by using the first image in the directory as a reference point,
and then using template matching to find where 0,0 is in each subsequent image.

The result is a JSON file with the pixel-coords of the Minecraft world's center
in each image.
"""

from utils.match_template import match_template
import os
import cv2 as cv
import json
import imagesize
from tqdm import tqdm

# extend sys.path to include the parent directory
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# import locally from utils

INPUT_DIR = "../input/"
MAP_DIR = INPUT_DIR + "maps/"
CENTERS_DIR = INPUT_DIR + "centers/"

##################################################
ENABLE_SKIP_SAME_DIMENSIONS = True
"""
if True, we will skip template matching to determine whether the map has been
offset from the previous, if the dimensions of the curr image are the same
as the previous image.

In other words, this enables an optimisation where if dimensions are same
between neighbouring images, we assume the map has not moved and reuse the
offset from the previous image.
"""
##################################################


def main():
  first_image_path = MAP_DIR + os.listdir(MAP_DIR)[0]

  center_coords, template = prompt_for_img_center(first_image_path)
  if not center_coords:
    print("Failed to get center coordinates.")
    return
  print(f"Center coordinates of first image: {center_coords}")

  # get a dictionary of each image's center coordinates
  image_centers = align_all_images(center_coords, template)

  # write this information to a file
  if not os.path.exists(CENTERS_DIR):
    os.mkdir(CENTERS_DIR)

  output_path = CENTERS_DIR + "image_centers.json"
  with open(output_path, "w") as f:
    stringified = json.dumps(image_centers)
    f.write(stringified)
  print(f"Done! Written to {output_path}.")


def prompt_for_img_center(first_image_path: str):
  """
  Prompt the user to tell us, in pixel coordinates, what pixel in the image
  depicts the center of the minecraft map, ie: 0,0.
  """

  # select the first image in the directory
  if not first_image_path.endswith(".png"):
    return

  # load the image
  image: cv.Mat = cv.imread(first_image_path, 0)
  if image is None:
    print(f"Failed to load image {first_image_path}")
    return
  print(f"Loaded image {first_image_path}")

  # prompt user to tell us the coordinates of minecraft 0,0 in the image
  print("Please enter the coordinates of minecraft 0,0 in the image.")
  center_x = int(input("x: "))
  center_y = int(input("y: "))
  return ((center_x, center_y), image)


def align_all_images(center_coords: tuple[int, int], original_template: cv.Mat):
  """
  Loop through all images in the directory, and, using the user-inputed origin
  point on the first image as reference, use template matching to find where the
  origin point has moved to in each subsequent image.

  Returns a dict of each image's center coordinates.
  ```py
  {
    "image_name.png": (x, y),
  }
  ```
  """

  # dictionary of each image's center coordinates
  image_centers: dict[str, tuple[int, int]] = {}

  # make a copy of the original template
  template = original_template.copy()

  # every time we shift the image, we add the offset to this
  cumulative_offset = (0, 0)

  prev_iter_dims = None  # dimensions of the image in the previous iteration
  prev_file_name = None  # name of the image in the previous iteration

  # loop through all images in the directory
  file_loop = tqdm(os.listdir(MAP_DIR), unit="files")
  for file_name in file_loop:
    # skip non-png files
    if not file_name.endswith(".png"):
      continue

    """
    Use OpenCV template matching in order to find where the first image would
    fit in this image. Then, use that information (the offset) to find where
    0,0 has moved to in this image based on where it was in the first image.
    """

    # get dimensions of the current image
    curr_iter_dims = imagesize.get(MAP_DIR + file_name)

    # if the dimensions are the same as the previous image AND the optimisation
    # to skip these cases is enabled, we can skip, reusing the previous
    # iteration's center coordinates
    if ENABLE_SKIP_SAME_DIMENSIONS and prev_iter_dims == curr_iter_dims:
      image_centers[file_name] = image_centers[prev_file_name]
      file_loop.set_description(f"{file_name}: {image_centers[file_name]}")
      prev_file_name = file_name
      continue

    # match the template
    img_path = MAP_DIR + file_name
    top_left, _bottom_right = match_template(img_path, template)

    # this is how much the previous image has been shifted in the current image
    offset_to_prev = top_left
    new_center_coords = (
        center_coords[0] + cumulative_offset[0] + offset_to_prev[0],
        center_coords[1] + cumulative_offset[1] + offset_to_prev[1]
    )

    # add the offset to the cumulative offset
    cumulative_offset = (
        cumulative_offset[0] + offset_to_prev[0],
        cumulative_offset[1] + offset_to_prev[1]
    )

    image_centers[file_name] = new_center_coords
    file_loop.set_description(f"{file_name}: {new_center_coords}")

    template = cv.imread(img_path, 0)

    prev_iter_dims = curr_iter_dims
    prev_file_name = file_name

  return image_centers


if __name__ == "__main__":
  main()
