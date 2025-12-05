
        self.font = pygame.font.SysFont("arial", 16, bold=True)
        self.large_font = pygame.font.SysFont("arial", 30, bold=True)
        
        self.grid = Grid(w, h)
        self.bridge = Bridge()
        self.toolbar = Toolbar(w, h)
        self.graph = GraphOverlay(20, h - 250, 400, 150)
        self.prop_menu = PropertyMenu(w, h)