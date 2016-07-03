from PIL import Image

try:
    import pycuda
except ImportError:
    GPU_ACCELERATION_AVAILABLE = False
else:
    GPU_ACCELERATION_AVAILABLE = True

if GPU_ACCELERATION_AVAILABLE:
    import numpy as np
    import pycuda.autoinit
    import pycuda.gpuarray as gpuarray
    from pycuda.compiler import SourceModule

from mandelbrot import constants


def is_gpu_accelerated():
    return GPU_ACCELERATION_AVAILABLE


class GPUObject(object):

    _kernel_headers = """
        #include <pycuda-complex.hpp>
        #include <math.h>
        typedef pycuda::complex<float> complex;

        #define MAX_ITERATIONS %(MAX_ITERATIONS)s
        #define ESCAPE_RADIUS %(ESCAPE_RADIUS)s

    """ % ({'MAX_ITERATIONS': constants.MAX_ITERATIONS,
            'ESCAPE_RADIUS': constants.ESCAPE_RADIUS})

    _block_size = (64, 4, 1)

    def __init__(self, logger):
        self._logger = logger

    def _generate_kernel_module(self, kernel_code):
        return SourceModule('%s%s' % (self._kernel_headers, kernel_code))


GENERATING_KERNEL_CODE = """
    __device__ int _get_pixel_iterations(
            int width, int height, complex cmin, complex dc,
            int x, int y, complex & z) {
        float fx = x / (float)(width - 1),
              fy = y / (float)(height - 1);

        complex c = cmin + complex(fx * dc.real(), fy * dc.imag());
        z = c;

        int iteration = 0;
        while(iteration < MAX_ITERATIONS && abs(z) < ESCAPE_RADIUS) {
            z = z * z + c;
            iteration++;
        }

        return iteration;
    }

    __global__ void get_pixel_iterations(
            int * iterations, float * z_values,
            int width, int height,
            complex cmin, complex dc) {
        int x = threadIdx.x + blockDim.x * blockIdx.x;
        int y = threadIdx.y + blockDim.y * blockIdx.y;

        if (x < width && y < height) {
            complex cz;
            iterations[y * width + x] = _get_pixel_iterations(
                width, height, cmin, dc, x, y, cz);
            z_values[y * width + x] = abs(cz);
        }
    }
"""


class MandelbrotGeneratorGPU(GPUObject):

    def __init__(self, logger):
        GPUObject.__init__(self, logger)
        if not is_gpu_accelerated():
            return

        kernel_module = self._generate_kernel_module(GENERATING_KERNEL_CODE)
        self._get_pixel_iterations = kernel_module.get_function(
            'get_pixel_iterations')

    def generate(self, width, height, real_axis_range, imag_axis_range, tasks):
        if not is_gpu_accelerated():
            self._logger.error(
                'No GPU acceleration is available, please use CPU.')
            return

        iterations = np.empty(width * height, np.int32)
        iterations_gpu = gpuarray.to_gpu(iterations)

        z_values = np.empty(width * height, np.float32)
        z_values_gpu = gpuarray.to_gpu(z_values)

        cmin = complex(real_axis_range[0], imag_axis_range[0])
        cmax = complex(real_axis_range[1], imag_axis_range[1])
        dc = cmax - cmin

        dx, mx = divmod(width, self._block_size[0])
        dy, my = divmod(height, self._block_size[1])
        grid_size = ((dx + (mx > 0)), (dy + (my > 0)))

        self._get_pixel_iterations(
            iterations_gpu, z_values_gpu,
            np.int32(width), np.int32(height),
            np.complex64(cmin), np.complex64(dc),
            block=self._block_size, grid=grid_size)

        return (iterations_gpu, z_values_gpu, abs(dc))


RENDERING_KERNEL_CODE = """
    #define LOG_ESCAPE_RADIUS %(LOG_ESCAPE_RADIUS)s
    #define COLOR_DENSITY %(COLOR_DENSITY)s
    #define TOTAL_COLORS %(TOTAL_COLORS)s

    __device__ int _get_pixel_color(
            int iteration_count, float z_value, float dc,
            int * color_scheme) {
        float log_z = log2(z_value);
        float hue = iteration_count + 1 - abs(
            log2(log_z / LOG_ESCAPE_RADIUS));

        float color_density = COLOR_DENSITY;
        if (dc < 0.01)
        {
            color_density /= 4;
        }
        else if (dc < 0.04)
        {
            color_density /= 3;
        }
        else if (dc < 0.2)
        {
            color_density /= 2;
        }

        int color_index = int(color_density * hue);
        if (color_index >= TOTAL_COLORS) {
            color_index = TOTAL_COLORS - 1;
        }

        return color_scheme[color_index];
    }

    __global__ void get_pixel_color(
            int * colors, int * color_scheme,
            int * iterations, float * z_values,
            int width, int height, float dc) {
        int x = threadIdx.x + blockDim.x * blockIdx.x;
        int y = threadIdx.y + blockDim.y * blockIdx.y;

        if (x < width && y < height) {
            int iteration_count = iterations[y * width + x];
            if (iteration_count == MAX_ITERATIONS) {
                colors[y * width + x] = 0;
            } else {
                float z_value = z_values[y * width + x];

                colors[y * width + x] = _get_pixel_color(
                    iteration_count, z_value, dc, color_scheme);
            }
        }
    }
""" % ({'LOG_ESCAPE_RADIUS': int(constants.LOG_ESCAPE_RADIUS),
        'COLOR_DENSITY': constants.COLOR_DENSITY,
        'TOTAL_COLORS': constants.TOTAL_COLORS})


class MandelbrotRendererGPU(GPUObject):

    def __init__(self, logger):
        GPUObject.__init__(self, logger)
        if not is_gpu_accelerated():
            return

        kernel_module = self._generate_kernel_module(RENDERING_KERNEL_CODE)
        self._get_pixel_color = kernel_module.get_function(
            'get_pixel_color')

        color_scheme = np.asarray(constants.COLOR_SCHEME, np.int32)
        self._color_scheme_gpu = gpuarray.to_gpu(color_scheme)

    def render(self, width, height, results, tasks):
        if not is_gpu_accelerated():
            self._logger.error(
                'No GPU acceleration is available, please use CPU.')
            return

        image = Image.new('RGB', (width, height))

        iterations_gpu, z_values_gpu, dc = results

        colors = np.empty(width * height, np.int32)
        colors_gpu = gpuarray.to_gpu(colors)

        dx, mx = divmod(width, self._block_size[0])
        dy, my = divmod(height, self._block_size[1])
        grid_size = ((dx + (mx > 0)), (dy + (my > 0)))

        self._get_pixel_color(
            colors_gpu, self._color_scheme_gpu,
            iterations_gpu, z_values_gpu,
            np.int32(width), np.int32(height), np.float32(dc),
            block=self._block_size, grid=grid_size)

        colors = colors_gpu.get()

        # This is really slow, must be optimized
        image.putdata(colors.tolist())

        return image


class MandelbrotGPU(MandelbrotGeneratorGPU, MandelbrotRendererGPU):

    def __init__(self, logger):
        MandelbrotGeneratorGPU.__init__(self, logger)
        MandelbrotRendererGPU.__init__(self, logger)
