import cv2 as cv

def match_template(full_image_path: str, template: cv.Mat) -> tuple[tuple[int, int], tuple[int, int]]:
  """
  Finds the coordinates where the template image is most likely cropped from on
  the full image. Returns the top left and bottom right coordinates.
  https://docs.opencv.org/5.x/d4/dc6/tutorial_py_template_matching.html
  """
  img = cv.imread(full_image_path, 0)
  w, h = template.shape[::-1]

  res = cv.matchTemplate(img, template, cv.TM_CCOEFF)
  _min_val, _max_val, _min_loc, max_loc = cv.minMaxLoc(res)

  top_left = max_loc
  bottom_right = (top_left[0] + w, top_left[1] + h)

  return (top_left, bottom_right)
