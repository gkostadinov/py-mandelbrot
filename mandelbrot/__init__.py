import time
import logging

from mandelbrot import mandelbrot_cpu, mandelbrot_gpu

LOGGER = logging.getLogger('mandelbrot_visualisation')


class Mandelbrot(object):

    def __init__(self):
        self._logger = LOGGER

        self._cpu = mandelbrot_cpu.MandelbrotCPU(self._logger)
        self._gpu = mandelbrot_gpu.MandelbrotGPU(self._logger)

    def generate(self, width, height, real_axis_range, imag_axis_range,
                 tasks=1, gpu_acceleration=False):
        self._logger.debug(
            ('Mandelbrot set generation started with arguments:\n' +
             ' width: %s, height: %s\n' +
             ' real axis range: %s, imag axis range: %s')
            % (width, height, real_axis_range, imag_axis_range))

        self._logger.debug('Processes used in current run: %s' % tasks)

        gpu_acceleration = True \
            if gpu_acceleration and mandelbrot_gpu.is_gpu_accelerated() \
            else False

        mandelbrot_instance = self._cpu if not gpu_acceleration else self._gpu

        begin_time = time.time()

        begin_generation_time = time.time()
        results = mandelbrot_instance.generate(
            width, height, real_axis_range, imag_axis_range, tasks)
        generation_time = time.time() - begin_generation_time
        self._logger.info('Mandelbrot set generated in %.5fs'
                          % generation_time)

        begin_rendering_time = time.time()
        image = mandelbrot_instance.render(
            width, height, results, tasks)
        rendering_time = time.time() - begin_rendering_time
        self._logger.info('Mandelbrot set rendered in %.5fs'
                          % rendering_time)

        total_time = time.time() - begin_time
        self._logger.info('Total run time: %.5fs' % total_time)

        return image
