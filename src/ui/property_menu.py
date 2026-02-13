"""
Property menu for adjusting material and simulation parameters.
"""
import pygame
import math
from core.constants import *
from core.material_manager import MaterialManager


class Button:
    """Clickable button UI element."""
    
    def __init__(self, label, rect, callback):
        self.label = label
        self.rect = rect
        self.callback = callback
        self.hover = False

    def update(self, mouse_pos, mouse_down, mouse_click, scroll_y=0):
        scrolled_rect = self.rect.move(0, -scroll_y)
        self.hover = scrolled_rect.collidepoint(mouse_pos)
        if self.hover and mouse_click:
            self.callback()

    def draw(self, surface, scroll_y=0):
        scrolled_rect = self.rect.move(0, -scroll_y)
        color = (70, 80, 70) if self.hover else (50, 60, 50)
        
        pygame.draw.rect(surface, color, scrolled_rect, border_radius=6)
        border_col = COLOR_UI_BORDER if self.hover else (120, 120, 120)
        pygame.draw.rect(surface, border_col, scrolled_rect, 2, border_radius=6)
        
        font = pygame.font.SysFont("arial", 13, bold=True)
        txt = font.render(self.label, True, COLOR_TEXT_MAIN)
        tx = scrolled_rect.centerx - txt.get_width() // 2
        ty = scrolled_rect.centery - txt.get_height() // 2
        surface.blit(txt, (tx, ty))


class Slider:
    """
    Slider UI element for adjusting numeric values.
    
    Supports both linear and logarithmic scaling.
    """
    
    def __init__(self, label, unit, min_v, max_v, parent_dict, dict_key, is_log=False):
        self.label = label
        self.unit = unit
        self.min_v = min_v
        self.max_v = max_v
        self.parent_dict = parent_dict
        self.dict_key = dict_key
        self.dragging = False
        self.is_log = is_log

    def update(self, rect, mouse_pos, mouse_down):
        """Update slider value based on mouse interaction."""
        mx, my = mouse_pos
        
        if mouse_down:
            if rect.collidepoint(mx, my) or self.dragging:
                self.dragging = True
                ratio = (mx - rect.x) / rect.width
                ratio = max(0.0, min(1.0, ratio))
                
                # Convert ratio to value
                if self.is_log:
                    safe_min = max(1e-9, self.min_v)
                    new_val = safe_min * (self.max_v / safe_min) ** ratio
                else:
                    new_val = self.min_v + ratio * (self.max_v - self.min_v)
                
                self.parent_dict[self.dict_key] = new_val
        else:
            self.dragging = False

    def draw(self, surface, rect):
        """Render the slider."""
        curr = self.parent_dict.get(self.dict_key, 0.0)
        
        # Format display value with appropriate units
        display_val, display_unit = self._format_value(curr)
        
        # Render labels
        font = pygame.font.SysFont("arial", 12)
        label_txt = font.render(self.label, True, (200, 200, 200))
        val_txt = font.render(f"{display_val} {display_unit}", True, COLOR_TEXT_HIGHLIGHT)
        
        surface.blit(label_txt, (rect.x, rect.y - 18))
        surface.blit(val_txt, (rect.right - val_txt.get_width(), rect.y - 18))
        
        # Draw slider track
        pygame.draw.rect(surface, (30, 30, 30), rect, border_radius=4)
        
        # Calculate fill ratio
        ratio = self._value_to_ratio(curr)
        fill_w = int(rect.width * ratio)
        
        if fill_w > 0:
            fill_rect = (rect.x, rect.y, fill_w, rect.height)
            pygame.draw.rect(surface, (100, 150, 100), fill_rect, border_radius=4)
        
        # Draw handle
        handle_x = rect.x + fill_w
        pygame.draw.circle(surface, COLOR_UI_BORDER, (handle_x, rect.centery), 6)

    def _format_value(self, value):
        """Format value for display with appropriate unit."""
        display_val = value
        display_unit = self.unit
        
        # Special formatting for specific keys
        if self.dict_key == "E":
            display_val = value / 1e9
            display_unit = "GPa"
        elif self.dict_key == "strength":
            display_val = value / 1e6
            display_unit = "MPa"
        elif self.dict_key == "hollow_ratio":
            display_val = value * 100.0
            display_unit = "%"
        
        # Determine precision based on magnitude
        if abs(display_val) < 0.001:
            val_str = f"{display_val:.5f}"
        elif abs(display_val) < 0.1:
            val_str = f"{display_val:.3f}"
        elif abs(display_val) < 10.0:
            val_str = f"{display_val:.2f}"
        else:
            val_str = f"{display_val:.1f}"
        
        return val_str, display_unit

    def _value_to_ratio(self, value):
        """Convert current value to slider position ratio."""
        try:
            if self.is_log:
                safe_min = max(1e-9, self.min_v)
                safe_curr = max(safe_min, value)
                ratio = math.log(safe_curr / safe_min) / math.log(self.max_v / safe_min)
            else:
                ratio = (value - self.min_v) / (self.max_v - self.min_v)
            
            return max(0.0, min(1.0, ratio))
        except (ValueError, ZeroDivisionError):
            return 0.0


class PropertyMenu:
    """
    Scrollable property menu for adjusting simulation parameters.
    
    Contains sliders for material properties, global settings, and agent parameters.
    """
    
    # UI Layout constants
    MENU_WIDTH = 300
    SLIDER_GAP = 42
    BUTTON_HEIGHT = 35
    BUTTON_WIDTH = 240
    
    def __init__(self, screen_w, screen_h):
        self.w = self.MENU_WIDTH
        self.h = screen_h
        self.x = screen_w - self.w
        self.y = 0
        self.visible = False
        self.should_quit = False
        
        self.sliders = []
        self.scrollable_buttons = []
        self.fixed_buttons = []
        self.temp_slider = None
        
        # View modes
        self.view_mode = 1  # 0=Force, 1=Material, 2=Stress
        self.text_mode = 0  # 0=Values, 1=Percentage, 2=None
        
        # Scrolling
        self.scroll_y = 0
        self.scroll_area_top = 60
        self.scroll_area_bottom = self.h - 90
        self.content_padding_top = 30
        self.content_padding_bottom = 40
        
        self._setup_ui()

    def set_analysis_mode(self, enabled):
        """Switch temperature slider between base and simulation mode."""
        if enabled:
            self.temp_slider.dict_key = "sim_temp"
            self.temp_slider.label = "Szimulációs Hőmérséklet"
        else:
            self.temp_slider.dict_key = "base_temp"
            self.temp_slider.label = "Alap Hőmérséklet"

    def _create_centered_log_slider(self, label, unit, mat_key, prop_key, factor=20.0):
        """
        Create a logarithmic slider centered on the default value.
        
        Range: [default/factor, default*factor]
        """
        default_val = MaterialManager.MATERIALS[mat_key][prop_key]
        min_v = default_val / factor
        max_v = default_val * factor
        self.sliders.append(
            Slider(label, unit, min_v, max_v, 
                   MaterialManager.MATERIALS[mat_key], prop_key, is_log=True)
        )

    def _setup_ui(self):
        """Initialize all UI elements using data-driven approach."""
        # Material property definitions
        material_configs = [
            ("wood", "Fa", [
                ("Rugalmasság (E)", "Pa", "E", 20.0),
                ("Sűrűség", "kg/m³", "density", 10.0),
                ("Szakítószilárdság", "Pa", "strength", 20.0),
            ]),
            ("bamboo", "Bambusz", [
                ("Rugalmasság", "Pa", "E", 20.0),
                ("Sűrűség", "kg/m³", "density", 10.0),
                ("Szakítószilárdság", "Pa", "strength", 20.0),
            ]),
            ("steel", "Acél", [
                ("Rugalmasság", "Pa", "E", 20.0),
                ("Sűrűség", "kg/m³", "density", 10.0),
                ("Szakítószilárdság", "Pa", "strength", 20.0),
            ]),
            ("spaghetti", "Spagetti", [
                ("Rugalmasság (E)", "Pa", "E", 20.0),
                ("Sűrűség", "kg/m³", "density", 10.0),
                ("Szakítószilárdság", "Pa", "strength", 20.0),
            ]),
        ]
        
        # Create sliders for each material
        for mat_key, mat_name, props in material_configs:
            for prop_label, unit, prop_key, factor in props:
                label = f"{mat_name} {prop_label}"
                self._create_centered_log_slider(label, unit, mat_key, prop_key, factor)
            
            # Add thickness slider
            d_thick = MaterialManager.MATERIALS[mat_key]["thickness"]
            label = f"{mat_name} Átmérő"
            self.sliders.append(
                Slider(label, "m", d_thick/20.0, d_thick*20.0,
                       MaterialManager.MATERIALS[mat_key], "thickness", is_log=True)
            )
            
            # Add hollowness slider
            label = f"{mat_name} Üregesség"
            self.sliders.append(
                Slider(label, "%", 0.0, 0.99,
                        MaterialManager.MATERIALS[mat_key], "hollow_ratio")
            )
        
        # Global settings
        self.temp_slider = Slider(
            "Alap Hőm.", "°C", 0.0, 50.0,
            MaterialManager.SETTINGS, "base_temp"
        )
        self.sliders.append(self.temp_slider)
        
        # Agent properties
        d_mass = MaterialManager.AGENT["mass"]
        self.sliders.append(
            Slider("Ixchel Tömege", "kg", 0.1, 1500,
                   MaterialManager.AGENT, "mass", is_log=True)
        )
        self.sliders.append(
            Slider("Ixchel Sebessége", "m/s", 1.0, 20.0,
                   MaterialManager.AGENT, "speed")
        )
        
        # Calculate layout
        self._layout_elements()

    def _layout_elements(self):
        """Position buttons in the scrollable area."""
        current_y = self.scroll_area_top + self.content_padding_top
        sliders_h = len(self.sliders) * self.SLIDER_GAP
        button_start_y = current_y + sliders_h + 10
        
        # Scrollable buttons
        r1 = pygame.Rect(self.x + 30, button_start_y, 
                        self.BUTTON_WIDTH, self.BUTTON_HEIGHT)
        self.scrollable_buttons.append(
            Button("Nézet Váltása (V)", r1, self.toggle_view_mode)
        )
        
        r2 = pygame.Rect(self.x + 30, button_start_y + 45,
                        self.BUTTON_WIDTH, self.BUTTON_HEIGHT)
        self.scrollable_buttons.append(
            Button("Feliratok Váltása (T)", r2, self.toggle_text_mode)
        )
        
        # Fixed buttons (always visible)
        r_quit = pygame.Rect(self.x + 30, self.h - 70,
                            self.BUTTON_WIDTH, self.BUTTON_HEIGHT)
        self.fixed_buttons.append(Button("Kilépés", r_quit, self.trigger_quit))
        
        # Calculate total content height for scrolling
        last_element_bottom = button_start_y + 45 + self.BUTTON_HEIGHT + self.content_padding_bottom
        self.content_height = last_element_bottom - self.scroll_area_top

    def trigger_quit(self):
        """Signal that user wants to quit."""
        self.should_quit = True

    def toggle_view_mode(self):
        """Cycle through visualization modes."""
        self.view_mode = (self.view_mode + 1) % 3

    def toggle_text_mode(self):
        """Cycle through label modes."""
        self.text_mode = (self.text_mode + 1) % 3

    def toggle(self):
        """Show/hide the menu."""
        self.visible = not self.visible

    def handle_input(self, event):
        """
        Handle input events.
        
        Returns:
            True if event was consumed by menu, False otherwise
        """
        if not self.visible:
            return False
        
        mx, my = pygame.mouse.get_pos()
        
        # Only consume events if mouse is over menu
        if mx <= self.x:
            return False
        
        if event.type == pygame.MOUSEWHEEL:
            self._handle_scroll(event.y)
            return True
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Check fixed buttons
            for btn in self.fixed_buttons:
                if btn.rect.collidepoint(mx, my):
                    btn.callback()
                    return True
            
            # Check scrollable buttons
            if self.scroll_area_top <= my <= self.scroll_area_bottom:
                for btn in self.scrollable_buttons:
                    scrolled_rect = btn.rect.move(0, -self.scroll_y)
                    if scrolled_rect.collidepoint(mx, my):
                        btn.callback()
                        return True
        
        return True

    def _handle_scroll(self, scroll_amount):
        """Update scroll position."""
        scroll_speed = 25
        self.scroll_y -= scroll_amount * scroll_speed
        
        visible_h = self.scroll_area_bottom - self.scroll_area_top
        max_scroll = max(0, self.content_height - visible_h)
        self.scroll_y = max(0, min(self.scroll_y, max_scroll))

    def update(self):
        """Update interactive elements."""
        if not self.visible:
            return
        
        mx, my = pygame.mouse.get_pos()
        mouse_down = pygame.mouse.get_pressed()[0]
        mouse_in_view = (self.scroll_area_top <= my <= self.scroll_area_bottom) and (mx > self.x)
        
        # Update sliders
        start_y = self.scroll_area_top + self.content_padding_top
        for i, slider in enumerate(self.sliders):
            slider_y = start_y + i * self.SLIDER_GAP - self.scroll_y
            
            # Only update visible sliders
            if self.scroll_area_top - 25 < slider_y < self.scroll_area_bottom:
                rect = pygame.Rect(self.x + 30, slider_y, 240, 12)
                slider.update(rect, (mx, my), mouse_down and mouse_in_view)
        
        # Update buttons
        for btn in self.scrollable_buttons:
            if mouse_in_view:
                btn.update((mx, my), mouse_down, False, self.scroll_y)
            else:
                btn.hover = False
        
        for btn in self.fixed_buttons:
            btn.update((mx, my), mouse_down, False, 0)

    def draw(self, surface):
        """Render the property menu."""
        if not self.visible:
            return
        
        # Background
        from utils.render_utils import create_semi_transparent_surface
        bg = create_semi_transparent_surface(self.w, self.h, (35, 40, 35), 245)
        surface.blit(bg, (self.x, self.y))
        
        # Border
        pygame.draw.line(surface, COLOR_UI_BORDER, (self.x, 0), (self.x, self.h), 3)
        
        # Header
        font = pygame.font.SysFont("arial", 20, bold=True)
        header = font.render("Tulajdonságok", True, COLOR_TEXT_HIGHLIGHT)
        surface.blit(header, (self.x + 30, 20))
        pygame.draw.line(surface, (60, 60, 60),
                        (self.x + 20, 50), (self.x + self.w - 20, 50), 1)
        
        # Set clipping for scrollable area
        clip_rect = pygame.Rect(self.x, self.scroll_area_top, self.w,
                               self.scroll_area_bottom - self.scroll_area_top)
        surface.set_clip(clip_rect)
        
        # Draw sliders
        self._draw_sliders(surface)
        
        # Draw scrollable buttons
        for btn in self.scrollable_buttons:
            btn_scrolled_y = btn.rect.y - self.scroll_y
            if self.scroll_area_top - 40 < btn_scrolled_y < self.scroll_area_bottom:
                btn.draw(surface, self.scroll_y)
        
        # Draw mode info
        self._draw_mode_info(surface)
        
        # Clear clipping
        surface.set_clip(None)
        
        # Draw fixed buttons
        for btn in self.fixed_buttons:
            btn.draw(surface, 0)

    def _draw_sliders(self, surface):
        """Draw all sliders in the scrollable area."""
        start_y = self.scroll_area_top + self.content_padding_top
        
        for i, slider in enumerate(self.sliders):
            slider_y = start_y + i * self.SLIDER_GAP - self.scroll_y
            
            # Only draw visible sliders
            if slider_y > self.scroll_area_top - 40 and slider_y < self.scroll_area_bottom + 20:
                rect = pygame.Rect(self.x + 30, slider_y, 240, 12)
                slider.draw(surface, rect)

    def _draw_mode_info(self, surface):
        """Draw current view/text mode information."""
        if not self.scrollable_buttons:
            return
        
        last_btn = self.scrollable_buttons[-1]
        last_y = last_btn.rect.bottom - self.scroll_y
        
        if last_y >= self.scroll_area_bottom:
            return
        
        info_font = pygame.font.SysFont("arial", 12)
        
        # View mode
        v_modes = ["Erők (Kék/Piros)", "Anyagminta (Normál)", "Terhelés (Gradiens)"]
        v_str = f"Nézet: {v_modes[self.view_mode]}"
        v_txt = info_font.render(v_str, True, (180, 200, 180))
        surface.blit(v_txt, (self.x + 30, last_y + 10))
        
        # Text mode
        t_modes = ["Pontos Érték", "% Terhelés", "Nincs"]
        t_str = f"Adat: {t_modes[self.text_mode]}"
        t_txt = info_font.render(t_str, True, (180, 200, 180))
        surface.blit(t_txt, (self.x + 30, last_y + 25))