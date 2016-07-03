import os
import sys
import json

COLOR_PALETTE = [
    [202, 228, 62],
    [93, 200, 107],
    [48, 163, 140],
    [56, 102, 143],
    [95, 41, 100],
    [0, 0, 0]]


def linear_interpolation(color1, color2, left):
    if left == 0:
        return color1

    r1, g1, b1 = color1
    r2, g2, b2 = color2

    r_diff = r2 - r1
    g_diff = g2 - g1
    b_diff = b2 - b1

    r_inc = r_diff / float(left)
    g_inc = g_diff / float(left)
    b_inc = b_diff / float(left)

    return [r1 + r_inc, g1 + g_inc, b1 + b_inc]


def generate_colour_palette(total_colors=512):
    colors = []

    color_scheme = list(
        map(lambda x: list(map(lambda y: y / 255.0, x)), COLOR_PALETTE))
    part_length = int(total_colors / (len(color_scheme) - 1))

    for color_iterator in range(1, len(color_scheme)):
        colors.append(color_scheme[color_iterator - 1])
        for iterator in range(0, part_length):
            new_color = linear_interpolation(
                colors[-1], color_scheme[color_iterator],
                part_length - iterator)
            colors.append(new_color)

    integer_colors = []
    for color in colors:
        integer_colors.append(list(map(lambda x: int(x * 255), color)))

    return integer_colors[::-1]

RESOURCES_FOLDER = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', 'resources')
COLOR_SCHEME_FILE = os.path.join(RESOURCES_FOLDER, 'color_scheme.json')


def main():
    total_colors = 512
    if len(sys.argv) > 1:
        total_colors = int(sys.argv[1])

    colors = generate_colour_palette(total_colors)
    colors = [b * 65536 + g * 256 + r for r, g, b in colors]

    with open(COLOR_SCHEME_FILE, 'w') as color_scheme_file:
        json.dump(colors, color_scheme_file)

if __name__ == '__main__':
    main()
