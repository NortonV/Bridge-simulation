"""
Ixchel's Bridge - Engineering Laboratory

A physics-based bridge building and analysis simulation.
"""
import pygame
import sys
from core.constants import *
from core.grid import Grid
from core.game_state import GameState, GameMode
from core.material_manager import MaterialManager
from core.serializer import Serializer
from entities.bridge import Bridge
from entities.agent import Ixchel
from ui.editor import Editor
from ui.toolbar import Toolbar
from ui.graph_overlay import GraphOverlay
from ui.property_menu import PropertyMenu
from ui.renderers import AnalysisRenderer, VolumePopup
from solvers.static_solver import StaticSolver
from audio.audio_manager import AudioManager


class BridgeBuilderApp:
    """Main application class managing game loop and high-level state."""
    
    # Physics time step limit to prevent instability
    MAX_DT = 0.1
    
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Ixchel Hídja - Mérnöki Laboratórium")
        
        # Create fullscreen window
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        w, h = self.screen.get_size()
        
        self.clock = pygame.time.Clock()
        self.fonts = self._init_fonts()
        
        # Core systems
        self.grid = Grid(w, h)
        self.bridge = Bridge()
        self.state = GameState()
        
        # UI components
        self.toolbar = Toolbar(w, h)
        self.graph = GraphOverlay(20, h - 350, 400, 200, {"exaggeration": 100.0})
        self.prop_menu = PropertyMenu(w, h)
        
        # Simulation
        self.ghost_agent = Ixchel(None)  # Audio assigned later
        
        # Audio
        self.audio = self._init_audio()
        self.ghost_agent.audio = self.audio
        
        # Editor (needs audio)
        self.editor = Editor(self.grid, self.bridge, self.toolbar, self.audio)
        
        # Renderers
        self.analysis_renderer = AnalysisRenderer(self.grid, self.prop_menu)
        self.volume_popup = VolumePopup()
        
        # Create initial anchor points
        self._create_initial_anchors()

    def _init_fonts(self):
        """Initialize font objects."""
        return {
            'normal': pygame.font.SysFont("arial", 16, bold=True),
            'large': pygame.font.SysFont("arial", 30, bold=True),
        }

    def _init_audio(self):
        """Initialize audio system and load sounds."""
        audio = AudioManager()
        audio.load_music("theme.mp3")
        audio.play_music()
        audio.load_sfx("wood_place", "wood_place.mp3")
        audio.load_sfx("step", "step.mp3")
        audio.load_sfx("wood_break", "wood_break.mp3")
        return audio

    def _create_initial_anchors(self):
        """Create the two starting anchor points."""
        self.bridge.add_node(-15, 10, fixed=True)
        self.bridge.add_node(15, 10, fixed=True)

    def run(self):
        """Main game loop."""
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            # Clamp dt to prevent physics explosions
            dt = min(dt, self.MAX_DT)
            
            self.handle_input()
            self.update(dt)
            self.draw()

    def handle_input(self):
        """Process all input events."""
        mx, my = pygame.mouse.get_pos()
        world_pos = self.grid.snap(mx, my)
        keys = pygame.key.get_pressed()
        
        # Volume controls
        self._handle_volume_input(keys)
        
        # Continuous input (for delete tool)
        if self.state.is_build_mode:
            self.editor.handle_continuous_input(world_pos)
        
        # Discrete events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit()
            
            # Graph slider input
            if self.state.is_analysis_mode:
                self.graph.handle_input(event)
            
            # Property menu (consumes events if open)
            if self.prop_menu.handle_input(event):
                if self.prop_menu.should_quit:
                    self.quit()
                continue
            
            # Keyboard shortcuts
            if event.type == pygame.KEYDOWN:
                if self._handle_keyboard(event.key, keys):
                    continue
            
            # Mouse wheel for volume
            if event.type == pygame.MOUSEWHEEL:
                self._handle_scroll_volume(event.y)
            
            # Toolbar input
            self.toolbar.handle_input(event)
            
            # Editor input (build mode only)
            if self.state.is_build_mode:
                self.editor.handle_input(event, world_pos)
        
        # Agent input (analysis mode only)
        if self.state.can_simulate:
            self.ghost_agent.handle_input()

    def _handle_volume_input(self, keys):
        """Handle continuous volume adjustment."""
        if keys[pygame.K_UP]:
            self.audio.change_volume(0.01)
            self.state.update_volume_display(self.audio.volume)
        if keys[pygame.K_DOWN]:
            self.audio.change_volume(-0.01)
            self.state.update_volume_display(self.audio.volume)

    def _handle_keyboard(self, key, keys):
        """
        Handle keyboard shortcuts.
        
        Returns:
            True if event was handled, False otherwise
        """
        # Menu toggles
        if key in [pygame.K_ESCAPE, pygame.K_m]:
            self.prop_menu.toggle()
            return True
        
        # Arch mode toggle (build mode only)
        if key == pygame.K_a and self.state.is_build_mode:
            state_str = "BE" if self.editor.toggle_arch_mode() else "KI"
            self.state.show_status(f"Ív Eszköz: {state_str}")
            return True
        
        # View/text mode toggles
        if key == pygame.K_v:
            self.prop_menu.toggle_view_mode()
            return True
        if key == pygame.K_t:
            self.prop_menu.toggle_text_mode()
            return True
        
        # Simulation toggle
        if key == pygame.K_SPACE:
            if self.state.is_build_mode:
                self._start_simulation()
            else:
                self._stop_simulation()
            return True
        
        # Graph toggle
        if key == pygame.K_g:
            self.graph.toggle()
            return True
        
        # File operations (Ctrl+S, Ctrl+L)
        is_ctrl = (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL])
        if is_ctrl and self.state.is_build_mode:
            if key == pygame.K_s:
                self._save_file()
                return True
            if key == pygame.K_l:
                self._load_file()
                return True
        
        # Tool switches during analysis exit simulation
        if self.state.is_analysis_mode:
            if key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_x]:
                self._stop_simulation()
                return True
        
        return False

    def _handle_scroll_volume(self, scroll_y):
        """Handle mouse wheel volume adjustment."""
        if scroll_y != 0:
            change = scroll_y * 0.05
            self.audio.change_volume(change)
            self.state.update_volume_display(self.audio.volume)

    def _start_simulation(self):
        """Begin static analysis and simulation mode."""
        # Prepare solver
        solver = StaticSolver(self.bridge)
        
        # Check stability
        if not solver.is_stable():
            if "Mechanism" in solver.error_msg:
                self.state.show_error("Instabil szerkezet! (Mechanizmus)")
            else:
                self.state.show_error(solver.error_msg)
            return
        
        # Initial solve
        success = solver.solve(temperature=0.0, point_load=None)
        if not success:
            self.state.show_error("Instabil: Szinguláris Mátrix")
            return
        
        # Enter analysis mode
        self.state.enter_analysis_mode(solver)
        self.prop_menu.set_analysis_mode(True)  # Switch temp slider to sim mode
        self.graph.reset_data()
        self.graph.visible = True
        
        # Spawn agent at leftmost wood beam
        self._spawn_agent()
        
        agent_mass = MaterialManager.AGENT["mass"]
        self.state.show_status(f"Szimuláció (Tömeg: {agent_mass:.1f}kg)")

    def _spawn_agent(self):
        """Spawn agent at the leftmost wood beam."""
        start_node = None
        min_x = 9999
        
        for beam in self.bridge.beams:
            if beam.type == "wood":
                if beam.node_a.x < min_x:
                    min_x = beam.node_a.x
                    start_node = beam.node_a
                if beam.node_b.x < min_x:
                    min_x = beam.node_b.x
                    start_node = beam.node_b
        
        if start_node:
            self.ghost_agent.spawn(start_node.x, start_node.y + 1.0)
        else:
            self.ghost_agent.active = False

    def _stop_simulation(self):
        """Exit simulation mode and return to build mode."""
        self.state.enter_build_mode()
        self.toolbar.active_index = 0
        self.state.show_status("Épí­tés Mód")
        self.audio.stop_sfx("step")

    def _save_file(self):
        """Save bridge design to file."""
        success, msg = Serializer.save_as(self.bridge)
        if success:
            self.state.show_status(msg)
        else:
            self.state.show_error(msg)

    def _load_file(self):
        """Load bridge design from file."""
        success, msg = Serializer.open_file(self.bridge)
        if success:
            self.state.show_status(msg)
            self.graph.reset_data()
        else:
            self.state.show_error(msg)

    def update(self, dt):
        """Update game state and physics."""
        self.state.update(dt)
        self.prop_menu.update()
        
        if self.state.can_simulate:
            self._update_simulation(dt)

    def _update_simulation(self, dt):
        """Update physics simulation and check for failures."""
        solver = self.state.static_solver
        
        # Update agent mass from settings
        self.ghost_agent.mass = MaterialManager.AGENT["mass"]
        
        # Get current displacements and exaggeration
        displacements = solver.displacements
        exaggeration = self.graph.sim_settings["exaggeration"]
        
        # Update agent position
        load_info = self.ghost_agent.update_static(
            dt, self.bridge.beams, displacements, exaggeration
        )
        
        # Prepare loads for solver
        solver_loads = {}
        if load_info and 'beam' in load_info:
            solver_loads[load_info['beam']] = (load_info['t'], load_info['mass'])
        
        # Solve with thermal and point loads
        delta_T = MaterialManager.SETTINGS["sim_temp"] - MaterialManager.SETTINGS["base_temp"]
        solver.solve(temperature=delta_T, point_load=solver_loads)
        
        # Check for beam failures
        max_force = 0.0
        max_percent = 0.0
        new_break = False
        
        for beam in self.bridge.beams:
            # Calculate total load
            f_axial = abs(solver.results.get(beam, 0))
            f_bend = abs(solver.bending_results.get(beam, 0))
            total_load = f_axial + f_bend
            max_force = max(max_force, total_load)
            
            # Check stress ratio
            ratio = solver.stress_ratios.get(beam, 0)
            percent = ratio * 100.0
            max_percent = max(max_percent, percent)
            
            # Detect failure
            if ratio >= 1.0 and beam not in self.state.broken_beams:
                self.state.broken_beams.add(beam)
                new_break = True
        
        # Handle beam break
        if new_break:
            self.state.freeze_simulation()
            self.state.show_error("ELTÖRT! (Szimuláció Megállítva)")
            self.audio.play_sfx("wood_break")
            self.audio.stop_sfx("step")
        
        # Update graph
        self.graph.update(max_force, max_percent, "ANALYSIS")

    def draw(self):
        """Render the current frame."""
        self.grid.draw(self.screen)
        
        if self.state.is_build_mode:
            self._draw_build_mode()
        else:
            self._draw_analysis_mode()
        
        # Common UI
        self.toolbar.draw(self.screen)
        self.graph.draw(self.screen)
        self.prop_menu.draw(self.screen)
        
        # Messages
        self._draw_messages()
        
        # Volume popup
        self.volume_popup.draw(
            self.screen,
            self.state.volume_display_value,
            self.state.volume_timer
        )
        
        pygame.display.flip()

    def _draw_build_mode(self):
        """Draw build mode view."""
        self.editor.draw(self.screen)
        self._draw_build_hud()
        
        # Arch mode instructions
        if self.editor.arch_mode:
            self._draw_arch_instructions()

    def _draw_analysis_mode(self):
        """Draw analysis mode view."""
        # Render deformed structure
        self.analysis_renderer.draw(
            self.screen,
            self.bridge,
            self.state.static_solver,
            self.state.broken_beams,
            self.graph.sim_settings["exaggeration"]
        )
        
        # Draw agent
        if self.ghost_agent.active:
            from ui.renderers import draw_ixchel
            # Use visual_y for rendering (respects exaggeration)
            sx, sy = self.grid.world_to_screen(
                self.ghost_agent.x,
                self.ghost_agent.visual_y
            )
            draw_ixchel(self.screen, sx, sy)
        
        # Legend
        self._draw_legend()

    def _draw_build_hud(self):
        """Draw build mode HUD (node/beam count, shortcuts)."""
        # Stats
        info = f"Csomópontok: {len(self.bridge.nodes)} | Elemek: {len(self.bridge.beams)}"
        text = self.fonts['normal'].render(info, True, COLOR_AXIS)
        self.screen.blit(text, (20, 20))
        
        # Help text
        help_str = "SPACE: Szimuláció | M: Menü | A: ív Eszköz (Be/Ki) | G: Grafikon"
        help_txt = self.fonts['normal'].render(help_str, True, (80, 90, 80))
        w = self.screen.get_width()
        self.screen.blit(help_txt, (w - help_txt.get_width() - 20, 20))

    def _draw_arch_instructions(self):
        """Draw arch tool instructions."""
        msg = "ÍV ESZKÖZ (ARCH TOOL): BEKAPCSOLVA"
        hint = "1. Húzás: Szélesség | 2. Egér: Magasság"
        
        t1 = self.fonts['normal'].render(msg, True, (255, 200, 50))
        t2 = self.fonts['normal'].render(hint, True, (200, 200, 200))
        
        self.screen.blit(t1, (20, 50))
        self.screen.blit(t2, (20, 75))

    def _draw_legend(self):
        """Draw legend for analysis visualization."""
        from utils.render_utils import create_semi_transparent_surface
        
        x, y = 20, self.screen.get_height() - 480
        w, h = 220, 100
        
        # Background
        bg = create_semi_transparent_surface(w, h, (30, 35, 30), 230)
        self.screen.blit(bg, (x, y))
        pygame.draw.rect(self.screen, COLOR_UI_BORDER, (x, y, w, h), 2)
        
        # Title
        font = pygame.font.SysFont("arial", 14, bold=True)
        title = font.render("Jelmagyarázat", True, COLOR_TEXT_HIGHLIGHT)
        self.screen.blit(title, (x + 10, y + 10))
        
        # Legend items
        pygame.draw.rect(self.screen, COLOR_COMPRESSION, (x + 10, y + 35, 20, 20))
        lbl_c = font.render("Nyomás", True, (200, 200, 200))
        self.screen.blit(lbl_c, (x + 40, y + 35))
        
        pygame.draw.rect(self.screen, COLOR_TENSION, (x + 10, y + 65, 20, 20))
        lbl_t = font.render("Húzás", True, (200, 200, 200))
        self.screen.blit(lbl_t, (x + 40, y + 65))

    def _draw_messages(self):
        """Draw status/error messages."""
        if self.state.error_message:
            msg = self.state.error_message
            color = (255, 80, 80)
        elif self.state.status_message:
            msg = self.state.status_message
            color = (100, 255, 100)
        else:
            return
        
        from utils.render_utils import draw_text_with_background, create_semi_transparent_surface
        
        text = self.fonts['large'].render(msg, True, color)
        w = self.screen.get_width()
        
        # Create background
        bg = create_semi_transparent_surface(
            text.get_width() + 40,
            text.get_height() + 20,
            (20, 20, 20), 200
        )
        
        # Center at top
        pos = (w // 2, 100)
        text_rect = text.get_rect(center=pos)
        bg_rect = bg.get_rect(center=pos)
        
        pygame.draw.rect(self.screen, COLOR_UI_BORDER, bg_rect, 2, border_radius=10)
        self.screen.blit(bg, bg_rect)
        self.screen.blit(text, text_rect)

    def quit(self):
        """Clean shutdown."""
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    app = BridgeBuilderApp()
    app.run()