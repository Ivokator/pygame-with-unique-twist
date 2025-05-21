import pygame
import random
import sys

from constants import *

# LANDSCAPE CONSTANTS
NUM_SEGMENTS: int = 500
MIN_HEIGHT: int = SCREEN_HEIGHT // 4
MAX_HEIGHT: int = SCREEN_HEIGHT // 2
#
MOUNTAIN_COLOR: tuple[int, int, int] = (8, 5, 3)
OUTLINE_COLOR: tuple[int, int, int] = (137, 196, 152)
LINE_WIDTH: int = 3


def generate_peaks(world_width: int) -> list[tuple[int, int]]:
    """
    Returns a list of (x, y) points spanning 0 to world_width,
    with each segment flat or 45° slope.

    Arguments:
        world_width (int): The width of the world to generate peaks for.

    Returns:
        peaks (list[tuple[int, int]]): A list of (x, y) points representing the mountain peaks.
    """
    segment_w: int = world_width // NUM_SEGMENTS
    base_y: int = SCREEN_HEIGHT - random.randint(MIN_HEIGHT, MAX_HEIGHT)
    peaks: list[tuple[int, int]] = [(0, base_y)]

    for i in range(1, NUM_SEGMENTS + 1):
        slope: int = random.choice([-1, 0, 1])
        dy: int = slope * segment_w # delta y

        # calculate new y position based on previous peak
        y_prev: int = peaks[-1][1]
        y_new: int = y_prev + dy

        # clamp within vertical bounds
        y_min: int = SCREEN_HEIGHT - MAX_HEIGHT
        y_max: int = SCREEN_HEIGHT - MIN_HEIGHT

        y_new = max(y_min, min(y_max, y_new))
        peaks.append((i * segment_w, y_new))

    return peaks


def draw_mountains(surface: pygame.Surface, peaks: list[tuple[int, int]], offset_x: float, world_width: int = SCREEN_WIDTH * 3) -> None:
    """
    Draw the mountain silhouette shifted by camera offset.
    
    Arguments:
        surface (pygame.Surface): The surface to draw on.
        peaks (list[tuple[int, int]]): A list of (x, y) points representing the mountain peaks.
        offset_x (int): The camera x-axis offset to shift the peaks by.
        world_width (int): The width of the world to draw mountains for.

    """

    # shift peaks by offset
    shifted = [(x + offset_x - (world_width // 2), y) for x, y in peaks]

    # build polygon from left of view to right
    poly = [(shifted[0][0], SCREEN_HEIGHT), *shifted, (shifted[-1][0], SCREEN_HEIGHT)]

    # filled mountain
    pygame.draw.polygon(surface, MOUNTAIN_COLOR, poly)

    # outline
    for a, b in zip(shifted, shifted[1:]):
        pygame.draw.line(surface, OUTLINE_COLOR, a, b, LINE_WIDTH)


if __name__ == "__main__":

    # --------------- DEMO AUTO SCROLL ---------------

    def main() -> None:
        pygame.init()
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Scrolling Mountains")
        clock = pygame.time.Clock()

        # generate once for full world
        peaks = generate_peaks(SCREEN_WIDTH * 3)

        camera_x = 0
        scroll_speed = 1  # pixels per frame

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # simple auto-scroll for demo
            camera_x = (camera_x + scroll_speed) % SCREEN_WIDTH

            screen.fill((0, 0, 0))
            draw_mountains(screen, peaks, camera_x)
            pygame.display.flip()
            clock.tick(120)

        pygame.quit()
        sys.exit()

    main()
