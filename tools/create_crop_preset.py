import imagesize
import json
import logging
import pathlib
import shutil
import subprocess
import tempfile

import tkinter as tk
from tkinter import filedialog


PAINT_DOT_NET_PATH = "C:/Program Files/paint.net/PaintDotNet.exe"
MAPS_DIR = "../input/maps/"
ORIGINS_DIR = "../input/centers/"


def main():
  logging.basicConfig(level=logging.DEBUG,
                      format="[%(asctime)s] [%(levelname)s] %(message)s",
                      datefmt="%Y-%m-%d %H:%M:%S")

  # create a tkinter window but hide it
  root = tk.Tk()
  root.withdraw()

  input_image_path, origin_offsets_path = select_files(root)

  origin_offsets = None
  with open(origin_offsets_path, "r") as f:
    origin_offsets = json.load(f)

  image_name = pathlib.Path(input_image_path).name
  if image_name not in origin_offsets:
    logging.error(f"Image `{image_name}` not found in `{origin_offsets_path}`")
    exit(1)

  # Open a copy of the image in Paint.NET for the user to make a selection box.
  temp_image_path = make_temp_copy(input_image_path)
  open_paint_dot_net(temp_image_path)

  # Prompt the user for the selection box
  img_sel_box = prompt_selection_box(*imagesize.get(temp_image_path))

  offset = origin_offsets[image_name]
  sel_box_minecraft_coords = conv_img_sel_box_to_mc_coords(
      img_sel_box, (offset[0], offset[1]))

  print("\nx1,y1,x2,y2 format:")
  print(f"Received selbox in image coords: {img_sel_box}")
  print(f"Converted selbox in Minecraft coords: {sel_box_minecraft_coords}")

  crop_preset = prompt_preset_title_and_description(sel_box_minecraft_coords)

  # Print out the crop preset as JSON
  print(f"""
Here is the generated crop preset:
{json.dumps(crop_preset, indent=2)}""")


def select_files(root: tk.Tk):
  """
  Prompts the user to select an exported map image and a centers file (which is
  a JSON file which contains the pixel locations for zero-zero on each map).

  Returns the paths of the selected files.
  """

  input_image_path = filedialog.askopenfilename(filetypes=[("Images", "*.png")],
                                                initialdir=MAPS_DIR,
                                                title="Select a map export")
  root.update()
  logging.info(f"Selected `{input_image_path}` as map image")

  origin_offsets_path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")],
                                                   initialdir=ORIGINS_DIR,
                                                   title="Select a centers file",
                                                   initialfile="image_centers.json")
  root.update()
  logging.info(f"Selected `{origin_offsets_path}` as centers file")

  return input_image_path, origin_offsets_path


def make_temp_copy(original_path: str):
  """
  Makes a temporary copy of the image at `original_path` and returns the path of the copy.
  """

  temp_dir = tempfile.mkdtemp()
  logging.info(f"Created temp dir `{temp_dir}`")

  temp_image_path = shutil.copy(original_path, temp_dir)
  logging.info(f"Copied `{original_path}` to `{temp_image_path}`")

  return temp_image_path


def open_paint_dot_net(img_path: str):
  """
  Opens the image at `img_path` in Paint.NET.
  """

  print("\nNow opening Paint.NET; make a selection box and type in the coordinates below.\n")

  try:
    subprocess.Popen([PAINT_DOT_NET_PATH, img_path])
    logging.info(f"Opened `{img_path}` in Paint.NET")
  except FileNotFoundError:
    logging.error(f"Could not find Paint.NET at `{PAINT_DOT_NET_PATH}`")
    exit(1)


def prompt_selection_box(img_w, img_h):
  """
  Prompts the user to enter their selection box in x,y,w,h format.
  Checks that the selection box is valid (not out of bounds).

  Then, converts the selection box to and returns it at x1,y1,x2,y2 format.
  """

  sel_xyxy = None
  while True:
    try:
      inp = input("Enter selection box in x,y,w,h format: ")
      sel_xywh = tuple(int(x) for x in inp.split(","))
      if len(sel_xywh) != 4:
        raise ValueError

      # convert to x1,y1,x2,y2 format
      sel_xyxy = (
          sel_xywh[0],
          sel_xywh[1],
          sel_xywh[0] + sel_xywh[2],
          sel_xywh[1] + sel_xywh[3]
      )

      # make sure none of the corners are out of bounds
      if (sel_xyxy[0] <= 0
              or sel_xyxy[1] <= 0
              or sel_xyxy[2] > img_w
              or sel_xyxy[3] > img_h):
        raise ValueError("Selection box contains out-of-bounds coordinates")
      break
    except ValueError as e:
      logging.error(f"Invalid input: {e}")
      continue

  return sel_xyxy


def conv_img_sel_box_to_mc_coords(img_sel_box: tuple[int, int, int, int],
                                  origin_offset: tuple[int, int]):
  """
  Converts the **image selection box** in x1,y1,x2,y2 format to the
  corresponding Minecraft **in-game coordinates**.
  """

  x_off, y_off = origin_offset

  return (
      img_sel_box[0] - x_off,
      img_sel_box[1] - y_off,
      img_sel_box[2] - x_off,
      img_sel_box[3] - y_off
  )


def prompt_preset_title_and_description(mc_sel_box: tuple[int, int, int, int]):
  """
  Prompts the user to input a title and description for the crop preset.
  """

  title = input("Input title for this crop preset: ")
  description = input("Input description for this crop preset: ")

  return {
      "title": title,
      "description": description,
      "rect": mc_sel_box
  }


if __name__ == "__main__":
  main()
