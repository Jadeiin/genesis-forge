"""
SDL2-based gamepad implementation for genesis-forge.

This module provides a backward-compatible Gamepad class that wraps
the SDL2 controller event loop.
"""
from __future__ import annotations

import threading
from typing import TYPE_CHECKING

from genesis_forge.gamepads.common import Key
from genesis_forge.gamepads.sdl2 import ControllerEventLoop

if TYPE_CHECKING:
    pass

__all__ = ["Gamepad", "GamepadState", "Key", "ControllerEventLoop"]


class GamepadState:
    """Data from a gamepad - backward compatible with HID implementation."""

    NUM_AXES = 6  # leftx, lefty, rightx, righty, lefttrigger, righttrigger

    def __init__(self):
        self.axis_values: list[float] = [0.0] * self.NUM_AXES
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


class Gamepad:
    """
    SDL2-based gamepad controller with backward compatibility for the HID-based API.
    
    This implementation uses SDL2's controller API for better cross-platform support
    and standardized button/axis mappings. SDL2 automatically detects and connects to
    game controllers, so the legacy HID parameters (config, vendor_id, product_id)
    are now deprecated and ignored.
    
    Example::
    
        >>> gamepad = Gamepad()
        >>> gamepad.state
        GamepadState(axis=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0], buttons=[], dpad=None)
        >>> gamepad.state.axis(0)
        0.0
        >>> gamepad.state.buttons
        []
    """

    # SDL2 axis indices
    AXIS_LEFTX = 0
    AXIS_LEFTY = 1
    AXIS_RIGHTX = 2
    AXIS_RIGHTY = 3
    AXIS_TRIGGERLEFT = 4
    AXIS_TRIGGERRIGHT = 5

    def __init__(self, config=None, vendor_id=None, product_id=None, debug: bool = False):
        """
        Initialize the SDL2 gamepad.
        
        Args:
            config: Deprecated - ignored for SDL2 (kept for backward compatibility)
            vendor_id: Deprecated - ignored for SDL2 (kept for backward compatibility)
            product_id: Deprecated - ignored for SDL2 (kept for backward compatibility)
            debug: If True, print debug information
        """
        self._state = GamepadState()
        self._debug = debug
        self.is_running = True
        self._lock = threading.Lock()

        # Start the SDL2 event loop in a background thread
        self._event_loop = ControllerEventLoop(
            handle_key=self._handle_key,
            alive=threading.Event(),
        )
        self._event_loop.alive.set()
        self._read_thread = threading.Thread(target=self._event_loop.run, daemon=True)
        self._read_thread.start()

        if self._debug:
            print("SDL2 gamepad controller initialized")

    @property
    def state(self) -> GamepadState:
        """The current state of the gamepad."""
        with self._lock:
            return self._state

    def _handle_key(self, key: Key) -> None:
        """Handle a key event from the SDL2 controller."""
        with self._lock:
            if key.keytype == Key.AXIS:
                # Map SDL2 axis to our axis array
                axis_idx = key.index
                if axis_idx < len(self._state.axis_values):
                    self._state.axis_values[axis_idx] = key.value if key.value is not None else 0.0
                    
            elif key.keytype == Key.BUTTON:
                button_name = key.name or f"button_{key.index}"
                if key.value == 1:  # Button pressed
                    if button_name not in self._state.buttons:
                        self._state.buttons.append(button_name)
                else:  # Button released
                    if button_name in self._state.buttons:
                        self._state.buttons.remove(button_name)
                        
                # Handle D-pad buttons specially
                if button_name in ["dpup", "dpdown", "dpleft", "dpright"]:
                    if key.value == 1:
                        self._state.dpad = button_name.replace("dp", "").upper()
                    else:
                        self._state.dpad = None

        if self._debug:
            print(f"Key event: {key} -> {self._state}")

    def stop(self) -> None:
        """Stop reading gamepad input."""
        self.is_running = False
        self._event_loop.stop()

    def connect(self, vendor_id=None, product_id=None):
        """
        Compatibility method - SDL2 auto-connects to controllers.
        
        Args:
            vendor_id: Ignored for SDL2
            product_id: Ignored for SDL2
            
        Returns:
            True (SDL2 auto-connects)
        """
        return True

    def auto_connect(self):
        """Compatibility method - SDL2 auto-connects to controllers."""
        pass
