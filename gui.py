import logging
from PIL import Image
LOGGER = logging.getLogger('mandelbrot_visualisation')

PYQT_VERSION = None
GUI_AVAILABLE = False
GUI_OBJECT = object

try:
    import PyQt5
except ImportError:
    PYQT_VERSION = None
else:
    PYQT_VERSION = 5
    del PyQt5

if not PYQT_VERSION:
    try:
        import PyQt4
    except ImportError:
        PYQT_VERSION = None
    else:
        PYQT_VERSION = 4
        del PyQt4

if PYQT_VERSION in [4, 5]:
    if PYQT_VERSION == 5:
        from PyQt5.QtWidgets import (
            QApplication, QWidget, QLabel, QLineEdit, QPushButton,
            QVBoxLayout, QMessageBox, QBoxLayout, QInputDialog,
            QCheckBox)
        from PyQt5 import QtGui
    elif PYQT_VERSION == 4:
        from PyQt4 import QtGui
        from PyQt4.QtGui import (
            QApplication, QWidget, QLabel, QLineEdit, QPushButton,
            QVBoxLayout, QMessageBox, QBoxLayout, QInputDialog,
            QCheckBox)

    GUI_AVAILABLE = True
    GUI_OBJECT = QWidget

import mandelbrot


def is_gui_available():
    return GUI_AVAILABLE


class InvalidInputError(Exception):
    pass


class Window(GUI_OBJECT):

    def __init__(self, parent=None, arguments={}):
        super(Window, self).__init__(parent)
        self._logger = LOGGER
        self._arguments = arguments

        self._mandelbrot = mandelbrot.Mandelbrot()
        self._image = None
        self._label_image_maxsize = 500
        self._create_layout()

    def _get_argument(self, argument_name, default_value=None):
        if argument_name in self._arguments:
            return self._arguments[argument_name]

        return default_value

    def _create_layout(self):
        top_layout_top = QBoxLayout(0)
        label_width = QLabel('Width:')
        width_value = str(self._get_argument('width', 500))
        self._width_input = QLineEdit(text=width_value)
        top_layout_top.addWidget(label_width)
        top_layout_top.addWidget(self._width_input)

        top_layout_bottom = QBoxLayout(0)
        label_height = QLabel('Height:')
        height_value = str(self._get_argument('height', 500))
        self._height_input = QLineEdit(text=height_value)
        top_layout_bottom.addWidget(label_height)
        top_layout_bottom.addWidget(self._height_input)

        center_layout_top = QBoxLayout(0)
        label_range_real = QLabel('Real axis range:')
        real_axis_range = self._get_argument('real_axis_range', [-2.0, 1.0])
        self._range_real1_input = QLineEdit(
            text=str(real_axis_range[0]), placeholderText='real.a')
        self._range_real2_input = QLineEdit(
            text=str(real_axis_range[1]), placeholderText='real.b')
        center_layout_top.addWidget(label_range_real)
        center_layout_top.addWidget(self._range_real1_input)
        center_layout_top.addWidget(self._range_real2_input)

        center_layout_bottom = QBoxLayout(0)
        label_range_imag = QLabel('Imaginary axis range:')
        imag_axis_range = self._get_argument('imag_axis_range', [-1.5, 1.5])
        self._range_imag1_input = QLineEdit(
            text=str(imag_axis_range[0]), placeholderText='imag.a')
        self._range_imag2_input = QLineEdit(
            text=str(imag_axis_range[1]), placeholderText='imag.b')
        center_layout_bottom.addWidget(label_range_imag)
        center_layout_bottom.addWidget(self._range_imag1_input)
        center_layout_bottom.addWidget(self._range_imag2_input)

        bottom_layout_top = QBoxLayout(0)
        label_tasks = QLabel('Number of tasks:')
        tasks_value = str(self._get_argument('tasks', 1))
        self._tasks_input = QLineEdit(text=tasks_value)
        bottom_layout_top.addWidget(label_tasks)
        bottom_layout_top.addWidget(self._tasks_input)

        self._gpu_checkbox = None
        gpu_value = self._get_argument('gpu', 0)
        if gpu_value:
            self._gpu_checkbox = QCheckBox('GPU acceleration')
            self._gpu_checkbox.setChecked(gpu_value)
            bottom_layout_top.addWidget(self._gpu_checkbox)

        bottom_layout_bottom = QVBoxLayout()
        self._process_btn = QPushButton('Process')
        self._process_btn.setDefault(True)
        bottom_layout_bottom.addWidget(self._process_btn)
        self._process_btn.clicked.connect(self._process_mandelbrot)

        image_layout = QVBoxLayout()
        self._image_label = QLabel()
        self._image_label.setVisible(False)

        self._save_btn = QPushButton('Save')
        self._save_btn.clicked.connect(self._save_visualisation)
        self._save_btn.setVisible(False)
        image_layout.addWidget(self._image_label)
        image_layout.addWidget(self._save_btn)

        mainLayout = QVBoxLayout()
        mainLayout.addLayout(top_layout_top)
        mainLayout.addLayout(top_layout_bottom)
        mainLayout.addLayout(center_layout_top)
        mainLayout.addLayout(center_layout_bottom)
        mainLayout.addLayout(bottom_layout_top)
        mainLayout.addLayout(bottom_layout_bottom)
        mainLayout.addLayout(image_layout)

        self.setLayout(mainLayout)
        self.setWindowTitle('Mandelbrot Visualisation')

    def _validate_input(self, input_data, input_name,
                        datatype=int, validate_value=True):
        if input_data == '':
            QMessageBox.information(self, 'Empty input',
                                    'Please enter %s.' % input_name)
            raise InvalidInputError('Empty input for %s' % input_name)

        try:
            input_value = datatype(input_data)

            if validate_value and input_value <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.information(self, 'Invalid %s' % input_name,
                                    ('Please enter a valid ' +
                                     'value for %s' % input_name))
            raise InvalidInputError('Invalid value for %s' % input_name)

        return input_value

    def _process_mandelbrot(self):
        tasks_count = self._tasks_input.text()
        width = self._width_input.text()
        height = self._height_input.text()
        real_axis_range = (
            self._range_real1_input.text(), self._range_real2_input.text())
        imag_axis_range = (
            self._range_imag1_input.text(), self._range_imag2_input.text())

        try:
            tasks_count = self._validate_input(
                tasks_count, 'number of tasks')
            width = self._validate_input(
                width, 'width')
            height = self._validate_input(
                height, 'height')
            real_axis_range = (
                self._validate_input(
                    real_axis_range[0], 'x.a range', float, False),
                self._validate_input(
                    real_axis_range[1], 'x.b range', float, False))
            imag_axis_range = (
                self._validate_input(
                    imag_axis_range[0], 'y.a range', float, False),
                self._validate_input(
                    imag_axis_range[1], 'y.b range', float, False))
            gpu = True \
                if self._gpu_checkbox and self._gpu_checkbox.isChecked() \
                else False
        except InvalidInputError as ex:
            self._logger.error(ex)
            return

        self._image_label.setVisible(False)
        self._process_btn.setVisible(False)

        self._logger.debug(
            'Chosed: %s, %s, %s, %s, %s'
            % (tasks_count, width, height, real_axis_range, imag_axis_range))

        self._image = self._mandelbrot.generate(
            width, height, real_axis_range, imag_axis_range, tasks_count, gpu)

        image_ratio = height / float(width)
        label_image_width = self._label_image_maxsize
        label_image_height = int(label_image_width * image_ratio)

        data = self._image.resize(
            (label_image_width, label_image_height),
            Image.ANTIALIAS).tobytes('raw', 'RGB')
        qt_image = QtGui.QImage(
            data, label_image_width, label_image_height,
            QtGui.QImage.Format_RGB888)
        pixmap = QtGui.QPixmap.fromImage(qt_image)
        self._image_label.setPixmap(pixmap)

        self._process_btn.setVisible(True)
        self._save_btn.setVisible(True)
        self._image_label.setVisible(True)

    def _save_visualisation(self):
        if not self._image:
            self._save_btn.setVisible(False)
            return

        filename, ok = QInputDialog.getText(
            self, 'Save visualisation', 'Enter filename:')

        filename = str(filename).strip()
        if not filename:
            filename = self._get_argument('output_file', 'mandelbrot.png')

        if ok:
            try:
                self._image.save(filename)
            except KeyError:
                self._image.save('%s.png' % filename)


def start(arguments):
    import sys
    app = QApplication(sys.argv)

    screen = Window(arguments=arguments)
    screen.show()

    sys.exit(app.exec_())
