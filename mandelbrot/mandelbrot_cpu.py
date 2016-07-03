import cmath
import multiprocessing
from PIL import Image

from mandelbrot import constants


class CPUObject(object):

    def __init__(self, logger):
        self._logger = logger

    def _parallelize(self, tasks, func, data):
        try:
            with multiprocessing.Pool(tasks) as pool:
                results = pool.map(func, data)
        except AttributeError:
            # Python 2 support
            pool = multiprocessing.Pool(tasks)
            results = pool.map(func, data)
            pool.close()
            pool.join()

        return results


def _get_pixel_iterations(args):
    width, height, cmin, dc, x, y = args

    fx, fy = x / float(width - 1), y / float(height - 1)

    z = c = cmin + complex(fx * dc.real, fy * dc.imag)

    iteration = 0
    while iteration < constants.MAX_ITERATIONS and \
            abs(z) < constants.ESCAPE_RADIUS:
        z = z * z + c
        iteration += 1

    return iteration, abs(z), abs(dc)


class MandelbrotGeneratorCPU(CPUObject):

    def __init__(self, logger):
        CPUObject.__init__(self, logger)

    def generate(self, width, height, real_axis_range, imag_axis_range, tasks):
        cmin = complex(real_axis_range[0], imag_axis_range[0])
        cmax = complex(real_axis_range[1], imag_axis_range[1])
        dc = cmax - cmin

        pixel_jobs = [(width, height, cmin, dc, x, y)
                      for y in range(height)
                      for x in range(width)]

        return self._parallelize(tasks, _get_pixel_iterations, pixel_jobs)


def _get_pixel_color(args):
    iterations, z, dc = args

    if iterations == constants.MAX_ITERATIONS:
        color = 0
    else:
        log_z = cmath.log(z, 2)
        hue = iterations + 1 - abs(
            cmath.log(log_z / constants.LOG_ESCAPE_RADIUS, 2))

        color_density = constants.COLOR_DENSITY
        if dc < 0.01:
            color_density /= 4
        elif dc < 0.04:
            color_density /= 3
        elif dc <= 0.2:
            color_density /= 2

        color_index = int(color_density * hue)
        if color_index >= constants.TOTAL_COLORS:
            color_index = constants.TOTAL_COLORS - 1

        color = constants.COLOR_SCHEME[color_index]

    return color


class MandelbrotRendererCPU(CPUObject):

    def __init__(self, logger):
        CPUObject.__init__(self, logger)

    def render(self, width, height, results, tasks):
        image = Image.new('RGB', (width, height))

        pixels = self._parallelize(tasks, _get_pixel_color, results)
        image.putdata(pixels)

        return image


class MandelbrotCPU(MandelbrotGeneratorCPU, MandelbrotRendererCPU):

    def __init__(self, logger):
        MandelbrotGeneratorCPU.__init__(self, logger)
        MandelbrotRendererCPU.__init__(self, logger)
