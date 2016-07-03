import logging

LOGGER_FORMAT = '[%(asctime)-15s] [%(process)s] [%(levelname)s] %(message)s'

logging.basicConfig(format=LOGGER_FORMAT)
LOGGER = logging.getLogger('mandelbrot_visualisation')

import gui
import console
import mandelbrot


def get_arguments():
    import argparse
    parser = argparse.ArgumentParser(
        description='Generates visualisation for Mandelbrot set')

    parser.add_argument(
        '--size', '-s',
        type=str,
        default='500x500',
        help='the output image size, example format: 500x500')

    parser.add_argument(
        '--plane', '-p',
        type=str,
        default='-2.0:1.0:-1.5:1.5',
        help=('the real and imaginary axis range, ' +
              'example format: -2.0:1.0:-1.5:1.5'))

    parser.add_argument(
        '--tasks', '-t',
        type=int,
        default=1,
        help=('the number of concurrent CPU tasks to ' +
              'generate the visualisation'))

    parser.add_argument(
        '--output', '-o',
        type=str,
        default='mandelbrot.png',
        help='the output filename')

    parser.add_argument(
        '--quiet', '-q',
        type=int,
        default=0,
        help='quiet mode (no verbose logs)')

    parser.add_argument(
        '--mode', '-m',
        type=int,
        default=0,
        help='0 for GUI, 1 for console mode')

    if mandelbrot.mandelbrot_gpu.is_gpu_accelerated():
        parser.add_argument(
            '--gpu', '-g',
            type=int,
            default=0,
            help='GPU acceleration mode')

    parsed_args = parser.parse_args()
    return parsed_args


def parse_arguments():
    arguments = get_arguments()

    size = arguments.size.split('x')
    if len(size) != 2:
        LOGGER.error('The size argument is invalid. Valid format: 640x480')
        return

    try:
        width, height = list(map(int, size))
    except Exception as ex:
        LOGGER.error(ex)
        return

    plane = arguments.plane.split(':')
    if len(plane) != 4:
        LOGGER.error('The plane argument is invalid. Valid format: -2:2:-2:2')
        return

    try:
        real_axis_range, imag_axis_range = (
            list(map(float, plane[:2])), list(map(float, plane[2:])))
    except Exception as ex:
        LOGGER.error(ex)
        return

    tasks = arguments.tasks
    output_file = arguments.output
    quiet_mode = arguments.quiet
    app_mode = arguments.mode

    gpu = arguments.gpu if hasattr(arguments, 'gpu') else False

    return {
        'width': width, 'height': height,
        'real_axis_range': real_axis_range,
        'imag_axis_range': imag_axis_range,
        'output_file': output_file,
        'tasks': tasks, 'gpu': gpu,
        'app_mode': app_mode, 'quiet_mode': quiet_mode
    }


def main():
    arguments = parse_arguments()
    quiet_mode = arguments['quiet_mode']
    app_mode = arguments['app_mode']

    if quiet_mode:
        LOGGER.setLevel(logging.INFO)
    else:
        LOGGER.setLevel(logging.DEBUG)

    if app_mode == 0:
        if gui.is_gui_available():
            gui.start(arguments)
        else:
            app_mode = 1
            LOGGER.error(
                'No PyQt library exists! Continuing to console mode...')

    if app_mode == 1:
        console.start(arguments)


if __name__ == '__main__':
    main()
