import logging
from pathlib import Path

import numpy as np
from PySide6.QtGui import QColorSpace, QImage, QImageWriter

from mir_commander.builtin_extensions.molecular_visualizer.graphics_nodes.atom.atom import Atom

logger = logging.getLogger(__name__)


class InteratomicDistance:
    def __init__(self, atom1: Atom, atom2: Atom):
        self.atom1 = atom1
        self.atom2 = atom2
        self.value = 0.0


class InteratomicAngle:
    def __init__(self, atom1: Atom, atom2: Atom, atom3: Atom):
        self.atom1 = atom1
        self.atom2 = atom2
        self.atom3 = atom3
        self.value = 0.0


class InteratomicTorsion:
    def __init__(self, atom1: Atom, atom2: Atom, atom3: Atom, atom4: Atom):
        self.atom1 = atom1
        self.atom2 = atom2
        self.atom3 = atom3
        self.atom4 = atom4
        self.value = 0.0


class InteratomicOutOfPlane:
    def __init__(self, atom1: Atom, atom2: Atom, atom3: Atom, atom4: Atom):
        self.atom1 = atom1
        self.atom2 = atom2
        self.atom3 = atom3
        self.atom4 = atom4
        self.value = 0.0


def save_image(image: np.ndarray, file_path: str):
    channels = image.shape[2]
    image_format = {3: QImage.Format.Format_RGB888, 4: QImage.Format.Format_RGBA8888}[channels]
    image_data = image.tobytes()
    qt_image = QImage(
        image_data,
        image.shape[1],
        image.shape[0],
        image.shape[1] * channels,
        image_format,
    )
    qt_image.setColorSpace(QColorSpace(QColorSpace.NamedColorSpace.SRgb))

    writer = QImageWriter(file_path)
    if not writer.write(qt_image):
        logger.error("Could not save image: %s", writer.errorString())
        if writer.error() == QImageWriter.ImageWriterError.DeviceError:
            raise OSError(writer.errorString())
        if writer.error() == QImageWriter.ImageWriterError.UnsupportedFormatError:
            raise ValueError(writer.errorString())
        raise RuntimeError(writer.errorString())
