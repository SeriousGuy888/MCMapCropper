import json
import os
import cv2 as cv
from PIL import Image, ImageDraw, ImageFont
from tqdm import tqdm

from match_template import match_template

INPUT_DIR = "./input/"
OUTPUT_DIR = "./output/"

MAP_DIR = INPUT_DIR + "maps/"

TEMPLATE_DIR = INPUT_DIR + "templates/"
TEMPLATE_NAME = ""  # Leave empty to prompt user to specify

CENTERS_FILE_PATH = INPUT_DIR + "centers/image_centers.json"

FONT = ImageFont.truetype("./fonts/UbuntuMono-Regular.ttf", 24)

# ENABLE_INFO_ON_IMAGE = False


def main():
  template = get_template()
  center_offsets = get_center_offsets()

  first_crop_rect, first_offset = get_first_position(template)

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
    # if ENABLE_INFO_ON_IMAGE:
    #   img = add_img_info(img, file_name)

    if not os.path.exists(OUTPUT_DIR):
      os.mkdir(OUTPUT_DIR)
    output_path = OUTPUT_DIR + file_name
    img.save(output_path)

  print("Done!")


def get_first_position(template: cv.Mat) -> tuple[tuple[tuple[int, int], tuple[int, int]], tuple[int, int]]:
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

  if not os.path.exists(CENTERS_FILE_PATH):
    raise FileNotFoundError(f"Centers file `{CENTERS_FILE_PATH}` not found.")

  with open(CENTERS_FILE_PATH, "r") as f:
    return json.loads(f.read())


def get_template() -> cv.Mat:
  """
  If the default template name exists, read that as the template.
  Otherwise, prompt the user to choose one of the files from the folder.
  """

  template_name = TEMPLATE_NAME

  if not template_name:
    template_options = os.listdir(TEMPLATE_DIR)

    choice = ""
    input_message = "\n\nSelect template image to crop to:\n"

    for index, item in enumerate(template_options):
      input_message += f"{index+1}) {item}\n"
    input_message += "Enter number: "

    while choice.lower() not in map(str, range(1, len(template_options) + 1)):
      choice = input(input_message)
    template_name = template_options[int(choice) - 1]
    print("\n")

  template_path = TEMPLATE_DIR + template_name

  if not os.path.exists(template_path):
    raise FileNotFoundError(f"Template file `{template_path}` not found.")
  return cv.imread(template_path, 0)


# def add_img_info(img: Image, info_text: str, info_section_height: int = 35) -> Image:
#   """
#   Add a section at the top of the image with space to add some
#   extra text.
#   """

#   dimensions = (img.width, img.height + info_section_height)
#   new_img = Image.new("RGBA", dimensions, "black")
#   new_img.paste(img, (0, info_section_height))

#   d = ImageDraw.Draw(new_img)
#   d.text((10, 5), info_text, font=FONT, fill="lightgray")

#   return new_img


def crop_img(img: Image, top_left: tuple[int, int], bottom_right: tuple[int, int]) -> Image:
  crop_rect = (top_left[0], top_left[1], bottom_right[0], bottom_right[1])
  return img.crop(crop_rect)


if __name__ == "__main__":
  main()
