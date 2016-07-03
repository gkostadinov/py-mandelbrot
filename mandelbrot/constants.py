import os
import json
import math

MAX_ITERATIONS = 512
ESCAPE_RADIUS = 4
COLOR_DENSITY = int(10 * (MAX_ITERATIONS / 512))
LOG_ESCAPE_RADIUS = math.log(ESCAPE_RADIUS, 2)

RESOURCES_FOLDER = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', 'resources')
COLOR_SCHEME_FILE = os.path.join(RESOURCES_FOLDER, 'color_scheme.json')


def __load_color_scheme(color_scheme):
    if not os.path.exists(color_scheme):
        return []

    with open(color_scheme) as color_scheme_file:
        color_scheme = json.load(color_scheme_file)

    return color_scheme
COLOR_SCHEME = __load_color_scheme(COLOR_SCHEME_FILE)
TOTAL_COLORS = len(COLOR_SCHEME)
