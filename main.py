import os
import cv2 as cv
from typing import Tuple, TypeVar
from matplotlib import pyplot as plt
from PIL import Image
from tqdm import tqdm

INPUT_DIR = "./input/"
OUTPUT_DIR = "./output/"

MAP_DIR = INPUT_DIR + "maps/"
TEMPLATE_PATH = INPUT_DIR + "templates/worldborder_only.png"


def main():
  if not os.path.exists(TEMPLATE_PATH):
    raise FileNotFoundError(f"Template path `{TEMPLATE_PATH}` does not exist.")
  template = cv.imread(TEMPLATE_PATH, 0)

  files = tqdm(os.listdir(MAP_DIR), unit="images")
  for f in files:
    if not f.endswith(".png"):
      continue

    files.set_description(f"Cropping {f}...")

    img_path = MAP_DIR + f
    top_left, bottom_right = match_template(img_path, template)

    img = Image.open(img_path)

    crop_rect = (top_left[0], top_left[1], bottom_right[0], bottom_right[1])
    cropped_img = img.crop(crop_rect)
    cropped_img.save(OUTPUT_DIR + f)
  print("Done!")


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

  # cv.rectangle(img, top_left, bottom_right, 255, 2)
  # plt.subplot(121), plt.imshow(res, cmap="gray")
  # plt.title("Matching Result"), plt.xticks([]), plt.yticks([])
  # plt.subplot(122), plt.imshow(img, cmap="gray")
  # plt.title("Detected Point"), plt.xticks([]), plt.yticks([])
  # plt.show()

  return (top_left, bottom_right)


main()
