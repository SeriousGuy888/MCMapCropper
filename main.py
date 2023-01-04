import os
import cv2 as cv
from typing import Tuple
from PIL import Image, ImageDraw, ImageFont
from tqdm import tqdm

INPUT_DIR = "./input/"
OUTPUT_DIR = "./output/"

MAP_DIR = INPUT_DIR + "maps/"

TEMPLATE_DIR = INPUT_DIR + "templates/"
TEMPLATE_NAME = ""  # Leave empty to prompt user to specify

FONT = ImageFont.truetype("./fonts/UbuntuMono-Regular.ttf", 24)

ENABLE_INFO_ON_IMAGE = False


def main():
  template = get_template()

  files = tqdm(os.listdir(MAP_DIR), unit="images")
  for f in files:
    if not f.endswith(".png"):
      continue

    files.set_description(f"Cropping {f}...")

    img_path = MAP_DIR + f
    top_left, bottom_right = match_template(img_path, template)

    img = Image.open(img_path)
    img = crop_img(img, top_left, bottom_right)
    if ENABLE_INFO_ON_IMAGE:
      img = add_img_info(img, f)

    if not os.path.exists(OUTPUT_DIR):
      os.mkdir(OUTPUT_DIR)
    img.save(OUTPUT_DIR + f)
  print("Done!")


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


def add_img_info(img: Image, info_text: str, info_section_height: int = 35) -> Image:
  """
  Add a section at the top of the image with space to add some
  extra text.
  """

  dimensions = (img.width, img.height + info_section_height)
  new_img = Image.new("RGBA", dimensions, "black")
  new_img.paste(img, (0, info_section_height))

  d = ImageDraw.Draw(new_img)
  d.text((10, 5), info_text, font=FONT, fill="lightgray")

  return new_img


def crop_img(img: Image, top_left: Tuple[int, int], bottom_right: Tuple[int, int]) -> Image:
  crop_rect = (top_left[0], top_left[1], bottom_right[0], bottom_right[1])
  return img.crop(crop_rect)


def match_template(full_image_path: str, template: cv.Mat) -> Tuple[Tuple[int, int], Tuple[int, int]]:
  """
  Finds the coordinates where the template image is most likely cropped from on
  the full image. Returns the top left and bottom right coordinates.
  https://docs.opencv.org/5.x/d4/dc6/tutorial_py_template_matching.html
  """
  img = cv.imread(full_image_path, 0)
  w, h = template.shape[::-1]

  res = cv.matchTemplate(img, template, cv.TM_CCOEFF)
  min_val, max_val, min_loc, max_loc = cv.minMaxLoc(res)

  top_left = max_loc
  bottom_right = (top_left[0] + w, top_left[1] + h)

  return (top_left, bottom_right)


main()
