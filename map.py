import random
import math

import pygame as pg
import pygame.gfxdraw as gfxdraw

def smooth_step(weight):
    """Smoothstep interpolation function."""
    return weight * weight * (3 - 2 * weight)


def linear_interpolation(point_a, point_b, weight):
    """Linear interpolation between point_a and point_b by weight."""
    return point_a + weight * (point_b - point_a)


def perlin_noise_1d(width, amp=1.0, freq=1.0, octaves=1):
    """
    Generate a 1D Perlin noise list of length `width`.

    Parameters:
    - width (int): Number of samples in the output noise list.
    - amp (float): Base amplitude for the first octave.
    - freq (float): Base frequency for the first octave.
    - octaves (int): Number of octaves to sum.

    Returns:
    - List[float]: Noise values in the range roughly [-amp, +amp], summed over octaves.
    """
    # Initialize output noise array
    output = [0.0 for _ in range(width)]

    # For each octave, add finer details
    for octave in range(octaves):
        frequency = freq * (2 ** octave)
        amplitude = amp * (0.5 ** octave)
        gradients = {}

        for i in range(width):
            # Map sample index to x coordinate in noise space
            x = (i * frequency) / width
            x0 = math.floor(x)
            x1 = x0 + 1
            dx0 = x - x0
            dx1 = x - x1

            # Assign or retrieve random gradient at integer grid points
            if x0 not in gradients:
                gradients[x0] = random.uniform(0, 1.0)
            if x1 not in gradients:
                gradients[x1] = random.uniform(0, 1.0)

            g0 = gradients[x0]
            g1 = gradients[x1]

            # Compute influence (dot product) of gradients
            dot0 = g0 * dx0
            dot1 = g1 * dx1

            # Interpolate between contributions
            weight = smooth_step(dx0)
            sample = linear_interpolation(dot0, dot1, weight)

            # Accumulate into the output array
            output[i] += sample * amplitude

    return output

def get_mountain_params():
    """Get the parameters for the mountains."""
    width = 10000
    amp = 1
    freq = 10
    octaves = 15

    return width, amp, freq, octaves


def generate_mountains() -> list[float]:

    width, amp, freq, octaves = get_mountain_params()
    
    noise_data: list[float] = perlin_noise_1d(width, amp, freq, octaves)
    return noise_data

def draw_mountains(surface: pg.surface.Surface, noise_data: list[float], screen_height: int, offset: float | int) -> None:

    width, amp, freq, octaves = get_mountain_params()

    # Ensure no negative points
    noise_data = [max(0, value) for value in noise_data]
    points = [(i + offset, (screen_height - noise_data[i] / amp * screen_height) - screen_height // 8) for i in range(len(noise_data))]

    gfxdraw.filled_polygon(surface, points, (96, 135, 106))

    for i in range(1, len(noise_data)):
            pg.draw.line(
            surface=surface,
            color=(137, 196, 152),
            start_pos=(i - 1 + offset, screen_height - noise_data[i - 1] / amp * screen_height - (screen_height // 8)),
            end_pos=(i + offset, screen_height - noise_data[i] / amp * screen_height - (screen_height // 8)),
            width=3
            )
    
    


if __name__ == "__main__":
    # Initialize Pygame
    pg.init()
    screen = pg.display.set_mode((1280, 960))
    pg.display.set_caption("1D Perlin Noise")


    screen.fill((0, 0, 0))
    print(pg.font.get_fonts())
        
    draw_mountains(screen, generate_mountains(), 960, 0)
    pg.display.flip()
    
    running = True
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
        

    pg.quit()
