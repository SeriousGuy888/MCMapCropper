# partially based on
# - https://stackoverflow.com/a/8696558
# - https://www.reddit.com/drzukj

import json
from typing import Literal
import pygame
import pathlib

SCALE_INTERVAL = 1.25
MIN_SCALE = SCALE_INTERVAL ** -8
MAX_SCALE = SCALE_INTERVAL ** 8

# INPUT_IMAGE = "input/maps/2022-12-04.png"
INPUT_IMAGE = "input/maps/2023-04-08.png"
# INPUT_IMAGE = "input/maps/2023-07-26.png"

ORIGIN_OFFSETS_PATH = "input/centers/image_centers.json"


class State:
  def __init__(self):
    self.pos = (0, 0)
    self.scale = 1.0
    self.needs_redraw = True

  def screen_to_world(self, screen_x, screen_y):
    world_x = screen_x / self.scale + self.pos[0]
    world_y = screen_y / self.scale + self.pos[1]
    return (world_x, world_y)

  def world_to_screen(self, world_x, world_y):
    screen_x = (world_x - self.pos[0]) * self.scale
    screen_y = (world_y - self.pos[1]) * self.scale
    return (screen_x, screen_y)

  def zoom(self, direction: Literal["in", "out"]):
    mouse_x, mouse_y = pygame.mouse.get_pos()

    # the worldpos the mouse was pointing at before the zoom
    mouse_world_x_before, mouse_world_y_before = \
        self.screen_to_world(mouse_x, mouse_y)

    # conduct the zoom
    if direction == "in":
      self.scale *= SCALE_INTERVAL
    elif direction == "out":
      self.scale /= SCALE_INTERVAL

    if self.scale < MIN_SCALE:
      self.scale = MIN_SCALE
      return
    if self.scale > MAX_SCALE:
      self.scale = MAX_SCALE
      return

    # the worldpos the mouse is pointing at after the zoom
    mouse_world_x_after, mouse_world_y_after = \
        self.screen_to_world(mouse_x, mouse_y)

    # Find the difference between the before & after mouse world positions,
    # and move the image by that difference. This makes it so zooming in and
    # out zooms in and out centered on the mouse position.
    self.pos = (self.pos[0] + mouse_world_x_before - mouse_world_x_after,
                self.pos[1] + mouse_world_y_before - mouse_world_y_after)
    self.needs_redraw = True

  def redraw_img(self, screen: pygame.Surface, image: pygame.Surface):
    screen.fill("#beeeef")

    scale = self.scale
    rect = image.get_rect()
    w, h = rect.width, rect.height

    # bounds of the world visible on screen
    wl, wt = self.screen_to_world(0, 0)
    wr, wb = w / scale - 250, h / scale - 250

    # place visible parts on a new surface, which improves performance
    # because not the whole (potentially very big) image has to be
    # blitted every frame
    new_screen = pygame.Surface((wr, wb))
    new_screen.blit(image, (0, 0), (wl, wt, wr, wb))

    # blit the new surface onto the actual screen
    # keeping scale in mind, but position is already in screen coords
    # so it is just put at (0, 0)

    screen.blit(pygame.transform.scale(
        new_screen, (image.get_width(), image.get_height())), (0, 0))

    self.needs_redraw = False


# pygame setup
pygame.init()
clock = pygame.time.Clock()


def setup():
  screen = pygame.display.set_mode(
      (1280, 720), pygame.DOUBLEBUF | pygame.HWSURFACE)
  image = pygame.image.load(INPUT_IMAGE).convert()

  pygame.event.set_allowed([
      pygame.QUIT,
      pygame.MOUSEWHEEL,
      pygame.MOUSEBUTTONDOWN,
      pygame.MOUSEBUTTONUP,
      pygame.MOUSEMOTION,
  ])

  return screen, image


def main_loop(screen: pygame.Surface, image: pygame.Surface):
  is_running = True

  state = State()

  is_dragging_l = False
  drag_l_start = (0, 0)
  drag_l_end = (0, 0)
  is_dragging_r = False
  drag_r_start = (0, 0)
  # drag_r_end = (0, 0)

  # read origin offsets
  origin_offsets = {}
  with open(ORIGIN_OFFSETS_PATH, "r") as f:
    origin_offsets = json.load(f)

  image_name = pathlib.Path(INPUT_IMAGE).stem + ".png"
  if image_name not in origin_offsets:
    print(f"Image {image_name} not found in {ORIGIN_OFFSETS_PATH}")
    return
  print(f"Image {image_name} has origin offset {origin_offsets[image_name]}")

  while is_running:
    pygame.display.set_caption(f"FPS: {clock.get_fps():.0f}")

    # poll for events
    for event in pygame.event.get():
      match event.type:
        case pygame.QUIT:
          # stop looping if the user has closed the window
          is_running = False

        case pygame.MOUSEWHEEL:
          state.zoom("in" if event.y > 0 else "out")

        case pygame.MOUSEBUTTONDOWN:
          if event.button == 1:
            is_dragging_l = True
            drag_l_start = state.screen_to_world(*event.pos)
            drag_l_end = drag_l_start
          if event.button == 3:
            is_dragging_r = True
            drag_r_start = state.screen_to_world(*event.pos)

        case pygame.MOUSEBUTTONUP:
          if event.button == 1:
            is_dragging_l = False

            # (x1, y1, x2, y2)
            pixel_coords = tuple(int(x) for x in (*drag_l_start, *drag_l_end))
            print("Selection box:", pixel_coords)
            print("Minecraft coords:", [
                  pixel_coords[i] - origin_offsets[image_name][i % 2] for i in range(4)])

          if event.button == 3:
            is_dragging_r = False

        case pygame.MOUSEMOTION:
          if is_dragging_l:
            drag_l_end = state.screen_to_world(*event.pos)
          if is_dragging_r:
            drag_r_end = state.screen_to_world(*event.pos)
            # move the image
            state.pos = (state.pos[0] - (drag_r_end[0] - drag_r_start[0]),
                         state.pos[1] - (drag_r_end[1] - drag_r_start[1]))
            drag_r_start = state.screen_to_world(*event.pos)
            state.needs_redraw = True

    # draw image
    if state.needs_redraw:
      state.redraw_img(screen, image)

    # draw selection box
    if drag_l_start != drag_l_end:
      pygame.draw.rect(screen, "#000000",
                       pygame.Rect(state.world_to_screen(*drag_l_start),
                                   ((drag_l_end[0] - drag_l_start[0]) * state.scale,
                                   (drag_l_end[1] - drag_l_start[1]) * state.scale)),
                       3)
      state.needs_redraw = True

    # update display
    pygame.display.flip()

    # limit FPS to 60
    clock.tick(30)


if __name__ == "__main__":
  screen, image = setup()

  main_loop(screen, image)
  pygame.quit()
