import logging
import mandelbrot


def start(arguments):
    logger = logging.getLogger('mandelbrot_visualisation')

    width = arguments['width']
    height = arguments['height']
    real_axis_range = arguments['real_axis_range']
    imag_axis_range = arguments['imag_axis_range']
    tasks = arguments['tasks']
    gpu = arguments['gpu']
    output_file = arguments['output_file']

    mandelbrot_generator = mandelbrot.Mandelbrot()
    image = mandelbrot_generator.generate(
        width, height, real_axis_range, imag_axis_range, tasks, gpu)

    image.save(output_file)
    logger.info('Visualisation saved to %s' % output_file)
