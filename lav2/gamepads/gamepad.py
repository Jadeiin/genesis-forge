"""SDL2-based gamepad implementation."""

import threading
import time

try:
    import sdl2
    import sdl2.ext
    SDL2_AVAILABLE = True
except ImportError:
    SDL2_AVAILABLE = False

from .config import Button, GamepadState


# SDL2 button mapping to our Button enum
SDL_BUTTON_MAP = {
    sdl2.SDL_CONTROLLER_BUTTON_A: Button.A,
    sdl2.SDL_CONTROLLER_BUTTON_B: Button.B,
    sdl2.SDL_CONTROLLER_BUTTON_X: Button.X,
    sdl2.SDL_CONTROLLER_BUTTON_Y: Button.Y,
    sdl2.SDL_CONTROLLER_BUTTON_LEFTSHOULDER: Button.LB,
    sdl2.SDL_CONTROLLER_BUTTON_RIGHTSHOULDER: Button.RB,
    sdl2.SDL_CONTROLLER_BUTTON_BACK: Button.BACK,
    sdl2.SDL_CONTROLLER_BUTTON_START: Button.START,
    sdl2.SDL_CONTROLLER_BUTTON_GUIDE: Button.MODE,
    sdl2.SDL_CONTROLLER_BUTTON_LEFTSTICK: Button.LEFT_JOYSTICK,
    sdl2.SDL_CONTROLLER_BUTTON_RIGHTSTICK: Button.RIGHT_JOYSTICK,
    sdl2.SDL_CONTROLLER_BUTTON_DPAD_UP: Button.UP,
    sdl2.SDL_CONTROLLER_BUTTON_DPAD_DOWN: Button.DOWN,
    sdl2.SDL_CONTROLLER_BUTTON_DPAD_LEFT: Button.LEFT,
    sdl2.SDL_CONTROLLER_BUTTON_DPAD_RIGHT: Button.RIGHT,
}


class Gamepad:
    """
    SDL2-based gamepad controller.
    
    This implementation uses SDL2's game controller API which provides
    better cross-platform support and automatic button mapping.
    
    Example::
    
        >>> gamepad = Gamepad()
        >>> gamepad.state
        GamepadState(axis=[0.0, 0.0, 0.0, 0.0], buttons=['A'], dpad=UP)
        >>> gamepad.state.axis
        [0.0, 0.0, 0.0, 0.0]
        >>> gamepad.state.buttons
        ["A"]
        >>> gamepad.state.dpad
        "UP"
    """

    def __init__(self, debug: bool = False):
        """
        Initialize the SDL2 gamepad.
        
        Args:
            debug: If True, print debug information.
        """
        if not SDL2_AVAILABLE:
            raise ImportError(
                "SDL2 is not available. Install it with: pip install pysdl2 pysdl2-dll"
            )
        
        self._debug = debug
        self._state = GamepadState()
        self.is_running = True
        self._controller = None
        self._joystick = None
        
        # Initialize SDL2
        if sdl2.SDL_Init(sdl2.SDL_INIT_GAMECONTROLLER | sdl2.SDL_INIT_JOYSTICK) != 0:
            raise RuntimeError(f"Failed to initialize SDL2: {sdl2.SDL_GetError()}")
        
        # Connect to gamepad
        self.connect()
        
        # Start reading thread
        self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
        self.read_thread.start()

    @property
    def state(self) -> GamepadState:
        """The current state of the gamepad."""
        return self._state

    def connect(self) -> bool:
        """
        Attempt to connect to the first available game controller.
        
        Returns:
            True if connected successfully, False otherwise.
        """
        num_joysticks = sdl2.SDL_NumJoysticks()
        
        if num_joysticks == 0:
            raise IOError("No game controllers found")
        
        # Try to open the first available game controller
        for i in range(num_joysticks):
            if sdl2.SDL_IsGameController(i):
                self._controller = sdl2.SDL_GameControllerOpen(i)
                if self._controller:
                    self._joystick = sdl2.SDL_GameControllerGetJoystick(self._controller)
                    name = sdl2.SDL_GameControllerName(self._controller)
                    if name:
                        name_str = name.decode('utf-8') if isinstance(name, bytes) else str(name)
                        print(f"Connected to gamepad: {name_str}")
                    return True
        
        raise IOError("Could not connect to any game controller")

    def stop(self):
        """Stop reading gamepad input."""
        self.is_running = False

    def _read_loop(self):
        """Read gamepad input and update state."""
        while self.is_running:
            try:
                # Process SDL events
                event = sdl2.SDL_Event()
                while sdl2.SDL_PollEvent(event) != 0:
                    # We process events but state is read directly from controller
                    pass
                
                # Update state from controller
                if self._controller:
                    self._update_state()
                    
                    if self._debug:
                        print(self._state)
                
                # Small delay to prevent excessive CPU usage
                time.sleep(0.001)
                
            except Exception as e:
                print(f"Error in gamepad read loop: {e}")
        
        # Cleanup
        if self._controller:
            sdl2.SDL_GameControllerClose(self._controller)
        sdl2.SDL_Quit()

    def _update_state(self):
        """Update the gamepad state from SDL2 controller."""
        # Read axes
        # SDL2 axes are in range -32768 to 32767, normalize to -1.0 to 1.0
        axes = []
        for axis_id in [
            sdl2.SDL_CONTROLLER_AXIS_LEFTX,
            sdl2.SDL_CONTROLLER_AXIS_LEFTY,
            sdl2.SDL_CONTROLLER_AXIS_RIGHTX,
            sdl2.SDL_CONTROLLER_AXIS_RIGHTY,
        ]:
            value = sdl2.SDL_GameControllerGetAxis(self._controller, axis_id)
            # Normalize to -1.0 to 1.0
            normalized = value / 32768.0
            # Apply deadzone
            if abs(normalized) < 0.1:
                normalized = 0.0
            axes.append(normalized)
        
        # Read triggers (0 to 32767, normalize to 0.0 to 1.0)
        left_trigger = sdl2.SDL_GameControllerGetAxis(
            self._controller, sdl2.SDL_CONTROLLER_AXIS_TRIGGERLEFT
        ) / 32767.0
        right_trigger = sdl2.SDL_GameControllerGetAxis(
            self._controller, sdl2.SDL_CONTROLLER_AXIS_TRIGGERRIGHT
        ) / 32767.0
        
        self._state.axis_values = axes
        
        # Read buttons
        buttons = []
        for sdl_button, our_button in SDL_BUTTON_MAP.items():
            if sdl2.SDL_GameControllerGetButton(self._controller, sdl_button):
                buttons.append(our_button.name)
        
        # Add trigger buttons if pressed
        if left_trigger > 0.5:
            buttons.append(Button.LT.name)
        if right_trigger > 0.5:
            buttons.append(Button.RT.name)
        
        self._state.buttons = buttons
        
        # D-pad is handled as buttons in SDL2, extract dpad state
        dpad = None
        if Button.UP.name in buttons:
            dpad = "UP"
        elif Button.DOWN.name in buttons:
            dpad = "DOWN"
        elif Button.LEFT.name in buttons:
            dpad = "LEFT"
        elif Button.RIGHT.name in buttons:
            dpad = "RIGHT"
        
        self._state.dpad = dpad


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test the SDL2 Gamepad connection")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    args = parser.parse_args()
    
    gamepad = Gamepad(debug=args.debug)
    print("Gamepad connected. Press Ctrl+C to exit.")
    
    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        gamepad.stop()
        print("\nExiting...")
