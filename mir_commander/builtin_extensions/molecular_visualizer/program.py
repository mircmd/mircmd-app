import logging
from pathlib import Path
from typing import Any, cast

from OpenGL.GL import GL_VERSION, glGetString
from PIL import Image, ImageCms
from PySide6.QtGui import QIcon, QOffscreenSurface, QOpenGLContext, QStandardItem, QSurfaceFormat
from PySide6.QtWidgets import QWidget

from mir_commander.builtin_extensions.molecular_visualizer.config import Config
from mir_commander.builtin_extensions.molecular_visualizer.graphics.utils import Color4f
from mir_commander.builtin_extensions.molecular_visualizer.visualizer import Visualizer
from mir_commander.builtin_extensions.utils.data_structures.atomic_coordinates import (
    AddAtomAction,
    AtomicCoordinates,
    NewPositionAction,
    NewSymbolAction,
    RemoveAtomsAction,
    SwapAtomsIndicesAction,
    bytes_to_atomic_coordinates,
)
from mir_commander.builtin_extensions.utils.data_structures.volume_cube import bytes_to_volume_cube
from mir_commander.errors import ProgramError
from mir_commander.sdk.base_program import (
    BaseProgram,
    MessageChannel,
    NodeChangedAction,
)
from mir_commander.utils import sanitize_filename

logger = logging.getLogger(__name__)


class MolecularVisualizerProgram(BaseProgram):
    def __init__(self, all: bool = False, *args, **kwargs):
        self._check_opengl_version()

        super().__init__(*args, **kwargs)

        self.config = Config()

        self._all = all

        self._atomic_coordinates_nodes: list[QStandardItem] = []
        self._volume_cube_nodes: list[QStandardItem] = []

        self.visualizer = Visualizer(program=self, title=self.item.text(), config=self.config)

        self._molecule_index = 0

        if self.item.get_type() == "mircmd:chemistry:volume_cube":
            self._volume_cube_nodes.append(self.item)
            self.visualizer.set_volume_cube(bytes_to_volume_cube(self.item.get_data()))

        self._draw_node = self.item
        self._set_draw_node()
        self.visualizer.set_atomic_coordinates(self._get_draw_node_atomic_coordinates())
        self.visualizer.coordinate_axes_adjust_length()

    def _check_opengl_version(self):
        """Check if OpenGL version is 3.3 or higher"""
        surface_format = QSurfaceFormat()
        surface_format.setVersion(3, 3)
        surface_format.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)

        context = QOpenGLContext()
        context.setFormat(surface_format)

        if not context.create():
            raise ProgramError("Failed to create OpenGL context")

        surface = QOffscreenSurface()
        surface.setFormat(context.format())
        surface.create()

        if not context.makeCurrent(surface):
            raise ProgramError("Failed to make OpenGL context current")

        try:
            version_string = glGetString(GL_VERSION)
            if version_string is None:
                raise ProgramError("Failed to get OpenGL version")

            version_str = version_string.decode("utf-8").split()[0]
            major, minor = map(int, version_str.split(".")[:2])

            if (major, minor) < (3, 3):
                raise ProgramError(f"OpenGL 3.3 or higher is required (found {major}.{minor})")
        except ProgramError:
            raise
        except Exception as e:
            logger.error(f"Failed to check OpenGL version: {e}")
            raise ProgramError("Failed to check OpenGL version")
        finally:
            context.doneCurrent()
            surface.destroy()

    def _get_node(self, node_id: int) -> QStandardItem:
        for nodes_list in [self._atomic_coordinates_nodes, self._volume_cube_nodes]:
            for node in nodes_list:
                if node.get_id() == node_id:
                    return node
        raise ValueError(f"Node with id {node_id} not found")

    @property
    def _node_full_name(self) -> str:
        names = [self._draw_node.text()]
        parent_node = self._draw_node.parent()
        while parent_node:
            names.append(parent_node.text())
            parent_node = parent_node.parent()
        return "/".join(reversed(names))

    def _atomic_coordinates_node(
        self, index: int, parent: QStandardItem, counter: int = -1
    ) -> tuple[bool, int, QStandardItem]:
        """
        Finds node with `AtomicCoordinates` data structure
        """

        index = max(0, index)
        last_node = parent
        if not parent.hasChildren() and parent.get_type() == "mircmd:chemistry:atomic_coordinates":
            return True, 0, last_node
        else:
            for i in range(parent.rowCount()):
                node = cast(QStandardItem, parent.child(i))
                if node.get_type() == "mircmd:chemistry:atomic_coordinates":
                    last_node = node
                    counter += 1
                    if index == counter:
                        return True, counter, node
                elif self._all and node.hasChildren():
                    found, counter, last_node = self._atomic_coordinates_node(index, node, counter)
                    if found:
                        return found, counter, last_node
            return False, counter, last_node

    def _set_draw_node(self):
        _, self._molecule_index, self._draw_node = self._atomic_coordinates_node(self._molecule_index, self.item)
        self._atomic_coordinates_nodes = [self._draw_node]

    def _get_draw_node_atomic_coordinates(self) -> list[tuple[int, AtomicCoordinates]]:
        if self._draw_node.get_type() == "mircmd:chemistry:atomic_coordinates":
            return [(self._draw_node.get_id(), bytes_to_atomic_coordinates(self._draw_node.get_data()))]
        return []

    def set_prev_atomic_coordinates(self):
        if self._molecule_index > 0:
            self._molecule_index -= 1
            self._set_draw_node()
            self.update_window_title_signal.emit(self.get_title())
            self.visualizer.set_atomic_coordinates(self._get_draw_node_atomic_coordinates())

    def set_next_atomic_coordinates(self):
        self._molecule_index += 1
        node = self._draw_node
        self._set_draw_node()
        if node != self._draw_node:
            self.update_window_title_signal.emit(self.get_title())
            self.visualizer.set_atomic_coordinates(self._get_draw_node_atomic_coordinates())

    def save_image(
        self,
        t_filename: str,
        width: int,
        height: int,
        bg_color: Color4f | None = None,
        crop_to_content: bool = False,
        i_param: int = 0,
        rewrite: bool = True,
        instance_index: int = 0,
    ):
        t_filename = t_filename.replace("%n", sanitize_filename(self._node_full_name))
        t_filename = t_filename.replace("%i", str(i_param + instance_index).zfill(6))

        if rewrite is False and Path(t_filename).exists():
            self.send_message_signal.emit(MessageChannel.CONSOLE, self.tr("File already exists: {}").format(t_filename))
            return

        try:
            image = self.visualizer.render_to_image(width, height, bg_color, crop_to_content)
            profile = ImageCms.createProfile("sRGB")
            Image.fromarray(image).save(t_filename, icc_profile=ImageCms.ImageCmsProfile(profile).tobytes())
            self.send_message_signal.emit(MessageChannel.CONSOLE, self.tr("{} saved successfully").format(t_filename))
        except Exception as e:
            txt = self.tr("Error saving image {}").format(t_filename)
            logger.error(f"{txt}: {e}")
            self.send_message_signal.emit(MessageChannel.CONSOLE, txt)

    def get_title(self) -> str:
        return self._node_full_name

    def get_icon(self) -> QIcon:
        if self.item.get_type() == "mircmd:chemistry:volume_cube":
            return self.item.icon()
        return self._draw_node.icon()

    def action_event(self, action: str, data: dict[str, Any], instance_index: int):
        if action == "view.rotate_scene":
            self.visualizer.rotate_scene(**data)
        elif action == "view.scale_scene":
            self.visualizer.scale_scene(**data)
        elif action == "view.set_scene_rotation":
            self.visualizer.set_scene_rotation(**data)
        elif action == "view.set_scene_scale":
            self.visualizer.set_scene_scale(**data)
        elif action == "atom_labels.set_symbol_visible":
            self.visualizer.set_atom_symbol_visible(**data)
        elif action == "atom_labels.set_number_visible":
            self.visualizer.set_atom_number_visible(**data)
        elif action == "atom_labels.set_size":
            self.visualizer.set_label_size_for_all_atoms(**data)
        elif action == "atom_labels.set_offset":
            self.visualizer.set_label_offset_for_all_atoms(**data)
        elif action == "atom_labels.toggle_visibility_for_all_atoms":
            self.visualizer.toggle_labels_visibility_for_all_atoms(**data)
        elif action == "atom_labels.toggle_visibility_for_selected_atoms":
            self.visualizer.toggle_labels_visibility_for_selected_atoms(**data)
        elif action == "volume_cube.add_isosurface":
            self.visualizer.add_volume_cube_isosurface(**data)
        elif action == "volume_cube.set_isosurface_color":
            self.visualizer.set_volume_cube_isosurface_color(**data)
        elif action == "volume_cube.set_isosurface_visible":
            self.visualizer.set_volume_cube_isosurface_visible(**data)
        elif action == "volume_cube.remove_isosurface":
            self.visualizer.remove_volume_cube_isosurface(**data)
        elif action == "image.save":
            self.save_image(**data | {"instance_index": instance_index})
        elif action == "coordinate_axes.set_visible":
            self.visualizer.set_coordinate_axes_visible(**data)
        elif action == "coordinate_axes.set_labels_visible":
            self.visualizer.set_coordinate_axes_labels_visible(**data)
        elif action == "coordinate_axes.set_both_directions":
            self.visualizer.set_coordinate_axes_both_directions(**data)
        elif action == "coordinate_axes.set_to_center":
            self.visualizer.set_coordinate_axes_center(**data)
        elif action == "coordinate_axes.set_length":
            self.visualizer.set_coordinate_axes_length(**data)
        elif action == "coordinate_axes.set_thickness":
            self.visualizer.set_coordinate_axes_thickness(**data)
        elif action == "coordinate_axes.set_font_size":
            self.visualizer.set_coordinate_axes_font_size(**data)
        elif action == "coordinate_axes.set_color":
            self.visualizer.set_coordinate_axis_color(**data)
        elif action == "coordinate_axes.set_label_color":
            self.visualizer.set_coordinate_axis_label_color(**data)
        elif action == "coordinate_axes.set_text":
            self.visualizer.set_coordinate_axis_text(**data)
        elif action == "coordinate_axes.adjust_length":
            self.visualizer.coordinate_axes_adjust_length(**data)
        elif action == "appearance.set_bg_color":
            self.visualizer.set_background_color(**data)
        elif action == "appearance.set_style":
            self.visualizer.set_style(**data)
        else:
            logger.error("Unknown key: %s", action)

    def node_changed_event(self, node_id: int, action: NodeChangedAction):
        try:
            node_type = self._get_node(node_id).get_type()
        except ValueError:
            return

        if node_type == "mircmd:chemistry:atomic_coordinates":
            if isinstance(action, AddAtomAction):
                self.visualizer.build_molecule(node_id)
            elif isinstance(action, NewSymbolAction):
                self.visualizer.update_atomic_number(node_id, action.index)
            elif isinstance(action, NewPositionAction):
                self.visualizer.update_atom_position(node_id, action.index)
            elif isinstance(action, RemoveAtomsAction):
                self.visualizer.remove_atoms(node_id, action.indices)
            elif isinstance(action, SwapAtomsIndicesAction):
                self.visualizer.swap_atoms_indices(node_id, action.index_1, action.index_2)
            else:
                logger.warning("Unknown action: %s", action)

    def get_widget(self) -> QWidget:
        return self.visualizer

    @staticmethod
    def get_supported_node_types() -> list[str]:
        return ["mircmd:chemistry:atomic_coordinates", "mircmd:chemistry:volume_cube"]
