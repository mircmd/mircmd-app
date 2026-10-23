from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, TypeAdapter, ValidationError
from PySide6.QtCore import QSignalBlocker
from PySide6.QtWidgets import QWidget

from mir_commander.sdk.ui_dsl.schema import Root
from mir_commander.sdk.ui_dsl.widgets.base import BuildContext, ContentWidget, UiItem, Widget
from mir_commander.sdk.ui_dsl.widgets.table import TableOp
from mir_commander.sdk.ui_dsl.widgets.tree import TreeOp


class SetOp(BaseModel):
    op: Literal["set"]
    id: str
    props: dict[str, Any]


_OPS = TypeAdapter(list[Annotated[SetOp | TableOp | TreeOp, Field(discriminator="op")]])
# Fixed when the widget is built.
_FIXED_PROPS = {"id", "type"}


class PatchError(ValueError):
    """The patch is invalid; none of its operations is applied."""


class Builder:
    def __init__(self, root: Root, extension_path: Path, parent: QWidget | None):
        self._root = root
        self._context = BuildContext(extension_path, self._emit)
        self._widget = self._build_view(self._context, root, parent)

    def _build_view(self, context: BuildContext, root: Root, parent: QWidget | None) -> QWidget:
        if isinstance(root.item, Widget):
            return root.item.build(context, parent)
        else:
            container = QWidget(parent=parent)
            if layout := root.item.build(context, container):
                container.setLayout(layout)
            return container

    def _emit(self, action: str, payload: dict[str, Any]) -> None:
        print(action, payload)

    def patch(self, ops: Any) -> None:
        """Applies a list of operations to the built widgets, in order.

        {"op": "set", "id": ..., "props": {...}} changes properties of any widget; the operations on the rows
        and columns of a table and on the nodes of a tree are described in widgets/table.py and widgets/tree.py.
        The whole list is checked first and applied only if every operation is valid.
        """
        try:
            parsed = _OPS.validate_python(ops)
        except ValidationError as error:
            raise PatchError(f"invalid operations: {error}") from error

        # Each operation applies to the result of the previous ones: the models and the shapes of the content
        # of widgets after the operations checked so far, by id.
        models: dict[str, Widget[Any]] = {}
        shapes: dict[str, Any] = {}
        # What to apply, in order: id, the model after the operation, and the properties changed by a set
        # operation or the content operation.
        steps: list[tuple[str, Widget[Any], set[str] | TableOp | TreeOp]] = []
        for op in parsed:
            if op.id not in self._context.widgets:
                raise PatchError(f"{op.id!r} is not a widget of the view")
            model = models.get(op.id, self._context.widgets[op.id])
            try:
                if isinstance(op, SetOp):
                    if fixed := _FIXED_PROPS & op.props.keys():
                        raise PatchError(f"{op.id!r}: {', '.join(sorted(fixed))} cannot be changed")
                    if unknown := op.props.keys() - type(model).model_fields.keys():
                        raise PatchError(f"{op.id!r} has no properties {', '.join(sorted(unknown))}")
                    model = type(model).model_validate({**model.model_dump(), **op.props})
                    steps.append((op.id, model, set(op.props)))
                else:
                    built = self._context.widgets[op.id]
                    if not isinstance(model, ContentWidget) or not isinstance(built, ContentWidget):
                        raise PatchError(f"{op.id!r} has no content, {op.op} does not apply to it")
                    # The content is kept only by the widget, so its shape is taken from the built one.
                    shape = shapes[op.id] if op.id in shapes else built.shape()
                    model, shapes[op.id] = model.edited(op, shape)
                    steps.append((op.id, model, op))
            except PatchError:
                raise
            except ValueError as error:
                raise PatchError(f"{op.id!r}: {error}") from error
            models[op.id] = model

        # collect may now refer to other widgets.
        items: dict[str, UiItem] = {**self._context.widgets, **models}
        for model in models.values():
            try:
                model.check_collect(items)
            except ValueError as error:
                raise PatchError(str(error)) from error

        for id, model, change in steps:
            built = self._context.widgets[id]
            # Update the built model in place: the connected signals refer to it.
            for name in type(built).model_fields:
                setattr(built, name, getattr(model, name))
            # A value set by the program is not an action of the user.
            with QSignalBlocker(built.widget):
                if isinstance(change, set):
                    built.apply(change)
                else:
                    assert isinstance(built, ContentWidget)
                    built.apply_op(change)

    def get_widget(self) -> QWidget:
        return self._widget
