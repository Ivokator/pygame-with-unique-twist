import random
import math

import pygame as pg


def smooth_step(weight): return weight * weight * (3 - 2 * weight)

def linear_interpolation(point_a, point_b, weight): return point_a + weight * (point_b - point_a)

def generate_ground(width, amp, freq, octaves):
    """Generates a ground pattern using 1D Perlin noise."""

    noise = [0] * width
    for octave in range(octaves):
        # Generate noise
        noise = [random.random() for _ in range(width)]
        noise = [x * amp * math.sin(freq * x) for x in noise]

        # Smooth the noise
        smooth_noise = [smooth_step(x) for x in noise]

        # Interpolate the noise
        for i in range(1, width):
            weight = (i / width)
            noise[i] = linear_interpolation(noise[i - 1], noise[i], weight)
        # Add the noise to the final result
        for i in range(width):
            noise[i] += smooth_noise[i]
        

    return noise

if __name__ == "__main__":
    # Test functions
    width = 500
    amp = 5000
    freq = .1
    octaves = 3


    pg.init()
    width, height = 800, 200
    screen = pg.display.set_mode((width, height))
    pg.display.set_caption("1D Perlin Noise")

    noise_data = generate_ground(width, amp, freq, octaves)
    print(noise_data)
    running = True
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False

        screen.fill((0, 0, 0))

        # Draw mountains with noise data
        # Draw line from previous point to current point
        pg.draw.lines(screen, (255, 255, 255), False,
                      [(x, height - noise_data[x] / 2) for x in range(width)], 1)

        pg.display.flip()

    pg.quit()
