"""Configuration classes for SDL2 gamepads."""

from enum import Enum


class Button(Enum):
    """SDL2 gamepad buttons."""
    A = 1
    B = 2
    X = 3
    Y = 4
    LB = 5
    RB = 6
    LT = 7
    RT = 8
    BACK = 9
    START = 10
    MODE = 11
    UP = 12
    DOWN = 13
    LEFT = 14
    RIGHT = 15
    LEFT_JOYSTICK = 16
    RIGHT_JOYSTICK = 17


class DPad(Enum):
    """D-pad directions."""
    NONE = 0
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4


class GamepadState:
    """State of a gamepad."""

    def __init__(self):
        self.axis_values: list[float] = []
        self.buttons: list[str] = []
        self.dpad: str | None = None

    def axis(self, index: int) -> float:
        """
        Get the axis value at an index.
        
        Args:
            index: The index of the axis to get the value of.
            
        Returns:
            The value of the axis at the index.
        """
        if index >= len(self.axis_values):
            return 0.0
        return self.axis_values[index]

    def __repr__(self):
        return f"GamepadState(axis={self.axis_values}, buttons={self.buttons}, dpad={self.dpad})"
