"""
Game state management for mode transitions and shared state.
"""
from enum import Enum, auto


class GameMode(Enum):
    """Available game modes."""
    BUILD = auto()
    ANALYSIS = auto()


class GameState:
    """
    Centralized game state manager.
    
    Handles mode transitions, messages, and shared simulation state.
    """
    
    def __init__(self):
        self.mode = GameMode.BUILD
        
        # Messages
        self.status_message = None
        self.error_message = None
        self.message_timer = 0
        
        # Analysis state
        self.static_solver = None
        self.broken_beams = set()
        self.simulation_frozen = False
        
        # Volume display
        self.volume_timer = 0
        self.volume_display_value = 0.5
    
    def enter_build_mode(self):
        """Transition to build mode."""
        self.mode = GameMode.BUILD
        self.static_solver = None
        self.simulation_frozen = False
        self.broken_beams.clear()
    
    def enter_analysis_mode(self, solver):
        """Transition to analysis mode."""
        self.mode = GameMode.ANALYSIS
        self.static_solver = solver
        self.simulation_frozen = False
        self.broken_beams.clear()
    
    def freeze_simulation(self):
        """Freeze the physics simulation (after beam break)."""
        self.simulation_frozen = True
    
    def show_status(self, text, duration=180):
        """Show a status message (green)."""
        self.status_message = text
        self.error_message = None
        self.message_timer = duration
    
    def show_error(self, text, duration=180):
        """Show an error message (red)."""
        self.error_message = text
        self.status_message = None
        self.message_timer = duration
    
    def update_volume_display(self, volume):
        """Update volume display and reset timer."""
        self.volume_display_value = volume
        self.volume_timer = 120
    
    def update(self, dt):
        """Update timers (called each frame)."""
        if self.message_timer > 0:
            self.message_timer -= 1
            if self.message_timer == 0:
                self.error_message = None
                self.status_message = None
        
        if self.volume_timer > 0:
            self.volume_timer -= 1
    
    @property
    def is_build_mode(self):
        return self.mode == GameMode.BUILD
    
    @property
    def is_analysis_mode(self):
        return self.mode == GameMode.ANALYSIS
    
    @property
    def can_simulate(self):
        """Check if simulation can run (not frozen)."""
        return self.is_analysis_mode and not self.simulation_frozen