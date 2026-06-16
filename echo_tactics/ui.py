import pygame

from .constants import BG, CYAN, GREEN, MAP_VIEW_WIDTH, MUTED, PANEL, PANEL_2, RED, SCREEN_HEIGHT, SCREEN_WIDTH, WHITE, YELLOW


class UI:
    def __init__(self):
        self.font = pygame.font.Font(None, 24)
        self.big = pygame.font.Font(None, 54)
        self.mid = pygame.font.Font(None, 34)

    def draw_hud(self, surface, game):
        panel = pygame.Rect(MAP_VIEW_WIDTH, 0, SCREEN_WIDTH - MAP_VIEW_WIDTH, SCREEN_HEIGHT)
        pygame.draw.rect(surface, PANEL, panel)
        pygame.draw.line(surface, CYAN, panel.topleft, panel.bottomleft, 2)
        self.text(surface, "ECHO TACTICS", MAP_VIEW_WIDTH + 22, 18, CYAN, self.mid)
        self.text(surface, f"Turn {game.turn_manager.turn} / {game.turn_manager.phase.upper()}", MAP_VIEW_WIDTH + 22, 58, WHITE)
        selected = game.selected_unit
        if selected:
            self.text(surface, f"Active: {selected.name}", MAP_VIEW_WIDTH + 22, 94, GREEN)
            self.text(surface, f"AP {selected.ap}/{selected.max_ap}   HP {selected.hp}/{selected.max_hp}", MAP_VIEW_WIDTH + 22, 122, WHITE)
        y = 164
        for unit in game.players:
            color = GREEN if unit.alive else RED
            marker = ">" if unit == selected else " "
            self.text(surface, f"{marker} {unit.name}: HP {unit.hp} AP {unit.ap}", MAP_VIEW_WIDTH + 22, y, color)
            y += 26
        self.text(surface, "Sound Log", MAP_VIEW_WIDTH + 22, y + 16, CYAN)
        y += 48
        for line in game.sound_system.log:
            self.text(surface, line[:32], MAP_VIEW_WIDTH + 22, y, MUTED)
            y += 24
        self.text(surface, "Controls", MAP_VIEW_WIDTH + 22, SCREEN_HEIGHT - 180, CYAN)
        controls = ["Mouse: move/attack/open", "TAB: next unit", "SPACE: wait", "F: sonic scan", "ENTER: end turn", "ESC: pause"]
        for i, line in enumerate(controls):
            self.text(surface, line, MAP_VIEW_WIDTH + 22, SCREEN_HEIGHT - 150 + i * 22, MUTED)

    def draw_menu(self, surface, save_manager):
        surface.fill(BG)
        self.text(surface, "ECHO TACTICS", 90, 90, CYAN, self.big)
        self.text(surface, "Tactical stealth strategy driven by sound.", 94, 148, WHITE, self.mid)
        items = ["1-6: Start campaign level", "R: Random Mission", "Q: Quit"]
        for i, item in enumerate(items):
            pygame.draw.rect(surface, PANEL_2, (94, 230 + i * 58, 420, 42), border_radius=6)
            self.text(surface, item, 112, 240 + i * 58, WHITE)
        unlocked = save_manager.data.get("unlocked_levels", 1)
        self.text(surface, f"Unlocked campaign levels: {unlocked}/6", 96, 440, GREEN)
        self._draw_radar(surface, 840, 290)

    def draw_overlay_message(self, surface, title, lines):
        shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 170))
        surface.blit(shade, (0, 0))
        box = pygame.Rect(300, 170, 650, 330)
        pygame.draw.rect(surface, PANEL, box, border_radius=8)
        pygame.draw.rect(surface, CYAN, box, 2, border_radius=8)
        self.text(surface, title, box.x + 32, box.y + 28, CYAN, self.big)
        for i, line in enumerate(lines):
            self.text(surface, line, box.x + 34, box.y + 105 + i * 34, WHITE)

    def text(self, surface, text, x, y, color=WHITE, font=None):
        img = (font or self.font).render(str(text), True, color)
        surface.blit(img, (x, y))

    def _draw_radar(self, surface, cx, cy):
        for r in range(45, 210, 40):
            pygame.draw.circle(surface, (47, 230, 255, 45), (cx, cy), r, 1)
        pygame.draw.line(surface, (47, 230, 255), (cx, cy), (cx + 180, cy - 70), 2)
        pygame.draw.circle(surface, YELLOW, (cx + 135, cy - 52), 6)
