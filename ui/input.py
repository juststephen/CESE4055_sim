from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget
)

class NumericInputWidget(QWidget):
    """
    Input widget with a slider for updating values live.
    """
    # Value updated signal
    value_updated = Signal(float)

    def __init__(
        self,
        val_name: str,
        val_init: float | int,
        val_type: type = float,
        val_min: float = 0,
        val_max: float = 100,
        val_step: float = 1,
        parent: QWidget | None = None
    ) -> None:
        """
        Initialise widget.

        Parameters
        ----------
        val_name : str
            Value's name.
        val_init : float | int
            Value.
        val_type :
            Value's type.
        val_min : float, default: 0
            Minimum input value.
        val_max : float, default: 100
            Maximum input value.
        val_step : float, default: 1
            Input slider step size.
        parent : QWidget | None
            Optional parent widget.
        """
        super().__init__(parent)

        self.val_name = val_name
        self.val_type = val_type
        self.val_min = val_min
        self.val_max = val_max
        self.val_step = val_step
        self.updating: bool = False

        self.label = QLabel(val_name)

        if val_type == float:
            self.input = QDoubleSpinBox()
            self.input.setDecimals(3)
            self.input.setRange(float(val_min), float(val_max))
            self.input.setSingleStep(float(val_step))
            self.input.setValue(float(val_init))
        elif val_type == int:
            self.input = QSpinBox()
            self.input.setRange(int(val_min), int(val_max))
            self.input.setSingleStep(int(val_step))
            self.input.setValue(int(val_init))
        else:
            raise TypeError('val_type can only be float or int')

        # Slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(1000)
        self.slider.setSingleStep(1)

        # Set initial slider position
        self.set_slider_from_value(val_init)

        # Top layout for label and input
        top_layout = QHBoxLayout()
        top_layout.addWidget(
            self.label,
            alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
        )
        top_layout.addWidget(
            self.input,
            alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop
        )

        # Layout for top layout and slider
        layout = QVBoxLayout()
        layout.addLayout(
            top_layout,
        )
        layout.addWidget(
            self.slider,
            alignment=Qt.AlignmentFlag.AlignTop
        )

        # Frame to encompass the layout
        self.frame = QFrame()
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.frame.setLayout(layout)

        # Main layout to contain the frame
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.frame)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Connections
        self.input.valueChanged.connect(self.on_input_changed)
        self.slider.valueChanged.connect(self.on_slider_changed)
        self.slider.sliderReleased.connect(self.on_slider_released)

    def on_input_changed(self) -> None:
        """
        Input changge callback.
        """
        if self.updating:
            return
        value = self.input.value()
        self.set_slider_from_value(value)
        self.value_updated.emit(value)

    def on_slider_changed(self, pos: int) -> None:
        """
        Slider moving callback.

        Parameters
        ----------
        pos : int
            Slider position.
        """
        if self.updating:
            return
        value = self.value_from_slider(pos)
        self.set_input_value(value)

    def on_slider_released(self) -> None:
        """
        Slider release callback.
        """
        value = self.input.value()
        self.value_updated.emit(value)

    def set_input_value(self, value: float | int) -> None:
        """
        Update spinbox.

        Parameters
        ----------
        value : float | int
            Value to set the slider to.
        """
        self.updating = True
        self.input.setValue(value) # type: ignore
        self.updating = False

    def set_slider_from_value(self, value: float | int) -> None:
        """
        Convert value to slider position and set it.

        Parameters
        ----------
        value : float | int
            Value to set the slider to.
        """
        self.updating = True
        ratio = (value - self.val_min) / (self.val_max - self.val_min)
        pos = int(ratio * 1000)
        self.slider.setValue(pos)
        self.updating = False

    def value_from_slider(self, pos: int) -> float | int:
        """
        Convert slider position to a value.

        Parameters
        ----------
        pos : int
            Slider position.

        Returns
        -------
        value : float | int
            Converted value.
        """
        ratio = pos / 1000
        value = self.val_min + ratio * (self.val_max - self.val_min)
        if self.val_type == int:
            value = int(round(value))
        return value
