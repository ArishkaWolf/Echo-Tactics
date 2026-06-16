import math
from types import SimpleNamespace

import pygame

from .constants import (
    DOOR_SOUND,
    FPS,
    GREEN,
    MAP_VIEW_WIDTH,
    MOVE_SOUND,
    RED,
    SCAN_SOUND,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TILE_SIZE,
    WAIT_SOUND,
    YELLOW,
)
from .fog import FogOfWar
from .levels import LEVELS
from .particles import ParticleSystem
from .pathfinding import PathFinder
from .save_manager import SaveManager
from .sound_system import SoundSystem
from .tactical_map import TacticalMap
from .turn_manager import TurnManager
from .ui import UI
from .units import EnemyUnit, PlayerUnit


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Echo Tactics")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.ui = UI()
        self.save_manager = SaveManager()
        self.state = "menu"
        self.running = True
        self.level_index = 0
        self.level_name = ""
        self.level_objective = ""
        self.map = None
        self.pathfinder = None
        self.fog = None
        self.sound_system = SoundSystem()
        self.turn_manager = TurnManager()
        self.particles = ParticleSystem()
        self.players = []
        self.enemies = []
        self.heard_enemy_marks = {}
        self.selected_unit = None
        self.camera = SimpleNamespace(x=0.0, y=0.0)
        self.stats = {"turns": 1, "kills": 0, "scans": 0, "damage_taken": 0}
        self.reachable = {}
        self.terminal_used = False

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000
            self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()

    def start_level(self, index=None, random_mission=False):
        self.level_index = index if index is not None else -1
        if random_mission:
            self.map = TacticalMap.random_mission()
            self.level_name = "Random Mission"
            self.level_objective = "Adapt, secure terminal if present, and exit"
        else:
            data = LEVELS[index]
            self.map = TacticalMap(data["map"])
            self.level_name = data["name"]
            self.level_objective = data["objective"]
        self.pathfinder = PathFinder(self.map)
        self.fog = FogOfWar(self.map)
        self.sound_system = SoundSystem()
        self.turn_manager = TurnManager()
        self.particles = ParticleSystem()
        names = ["Vector", "Pulse", "Ghost"]
        starts = self.map.player_starts[:3] or [(1, 1), (1, 2), (1, 3)]
        self.players = [PlayerUnit(x, y, names[i]) for i, (x, y) in enumerate(starts[:3])]
        self.enemies = [EnemyUnit(x, y, f"Sentinel {i + 1}") for i, (x, y) in enumerate(self.map.enemy_starts)]
        self.selected_unit = self.turn_manager.current_unit(self.players)
        self.heard_enemy_marks = {}
        self.stats = {"turns": 1, "kills": 0, "scans": 0, "damage_taken": 0}
        self.terminal_used = False
        self.fog.update(self.players)
        self.reachable = self.pathfinder.reachable(self.selected_unit.pos, self.selected_unit.ap, self.all_units())
        self.center_camera()
        self.state = "playing"

    def all_units(self):
        return [u for u in self.players + self.enemies if u.alive]

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self.handle_key(event.key)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.handle_click(event.pos)

    def handle_key(self, key):
        if self.state == "menu":
            if pygame.K_1 <= key <= pygame.K_6:
                idx = key - pygame.K_1
                if idx < self.save_manager.data.get("unlocked_levels", 1):
                    self.start_level(idx)
            elif key == pygame.K_r:
                self.start_level(random_mission=True)
            elif key == pygame.K_q:
                self.running = False
        elif self.state == "playing":
            if key == pygame.K_ESCAPE:
                self.state = "paused"
            elif key == pygame.K_TAB:
                self.turn_manager.next_unit(self.players)
                self.selected_unit = self.turn_manager.current_unit(self.players)
                self.update_reachable()
            elif key == pygame.K_SPACE:
                self.wait_selected()
            elif key == pygame.K_f:
                self.scan_selected()
            elif key == pygame.K_RETURN:
                self.enemy_turn()
        elif self.state == "paused":
            if key == pygame.K_ESCAPE:
                self.state = "playing"
            elif key == pygame.K_q:
                self.state = "menu"
        elif self.state in ("victory", "defeat", "stats"):
            if key == pygame.K_RETURN:
                self.state = "menu"

    def handle_click(self, pos):
        if self.state != "playing" or self.turn_manager.phase != "player" or not self.selected_unit:
            return
        if pos[0] >= MAP_VIEW_WIDTH:
            return
        tx = int((pos[0] + self.camera.x) // TILE_SIZE)
        ty = int((pos[1] + self.camera.y) // TILE_SIZE)
        clicked_enemy = next((e for e in self.enemies if e.alive and e.pos == (tx, ty) and self.map.tile_at(tx, ty).visible), None)
        if clicked_enemy and self.selected_unit.can_attack(clicked_enemy, self.fog):
            before = clicked_enemy.alive
            self.selected_unit.attack(clicked_enemy, self.sound_system, self.particles)
            if before and not clicked_enemy.alive:
                self.stats["kills"] += 1
            self.after_player_action()
            return
        if self.try_open_door(tx, ty):
            self.after_player_action()
            return
        self.try_move_selected(tx, ty)

    def try_move_selected(self, tx, ty):
        unit = self.selected_unit
        if not unit or unit.ap <= 0:
            return
        if (tx, ty) not in self.reachable:
            return
        path = self.pathfinder.find_path(unit.pos, (tx, ty), units=self.all_units())
        cost = len(path) - 1
        if path and 0 < cost <= unit.ap:
            unit.move_along(path, cost)
            self.sound_system.add_event(*unit.pos, MOVE_SOUND, f"{unit.name} moved", "player")
            self.after_player_action()

    def try_open_door(self, tx, ty):
        unit = self.selected_unit
        if not unit or unit.ap < 1:
            return False
        if abs(unit.pos[0] - tx) + abs(unit.pos[1] - ty) != 1:
            return False
        if self.map.open_door_at(tx, ty):
            unit.ap -= 1
            self.sound_system.add_event(tx, ty, DOOR_SOUND, f"{unit.name} opened door", "player")
            return True
        return False

    def wait_selected(self):
        if self.selected_unit and self.selected_unit.ap > 0:
            self.sound_system.add_event(*self.selected_unit.pos, WAIT_SOUND, f"{self.selected_unit.name} waited", "player")
            self.selected_unit.ap = 0
            self.after_player_action()

    def scan_selected(self):
        unit = self.selected_unit
        if not unit or unit.ap < 2:
            return
        unit.ap -= 2
        self.stats["scans"] += 1
        self.sound_system.add_event(*unit.pos, SCAN_SOUND, f"{unit.name} sonic scan", "player")
        for enemy in self.enemies:
            if enemy.alive:
                power = SCAN_SOUND - math.dist(unit.pos, enemy.pos)
                if power > 2:
                    self.heard_enemy_marks[enemy.pos] = 2.5
        self.after_player_action()

    def after_player_action(self):
        self.fog.update(self.players)
        self.update_reachable()
        self.check_objectives()
        if self.selected_unit and self.selected_unit.ap <= 0:
            self.turn_manager.next_unit(self.players)
            self.selected_unit = self.turn_manager.current_unit(self.players)
            self.update_reachable()
        if all(not u.alive or u.ap <= 0 for u in self.players):
            self.enemy_turn()

    def enemy_turn(self):
        self.turn_manager.start_enemy_turn()
        hp_before = sum(u.hp for u in self.players if u.alive)
        for enemy in self.enemies:
            enemy.take_turn(self)
        hp_after = sum(u.hp for u in self.players if u.alive)
        self.stats["damage_taken"] += max(0, hp_before - hp_after)
        self.turn_manager.start_player_turn(self.players)
        self.stats["turns"] = self.turn_manager.turn
        self.selected_unit = self.turn_manager.current_unit(self.players)
        self.fog.update(self.players)
        self.update_reachable()
        self.check_objectives()

    def update(self, dt):
        if self.state != "playing":
            return
        self.sound_system.update(dt)
        self.particles.update(dt)
        for unit in self.all_units():
            unit.update_animation(dt)
        for pos in list(self.heard_enemy_marks):
            self.heard_enemy_marks[pos] -= dt
            if self.heard_enemy_marks[pos] <= 0:
                del self.heard_enemy_marks[pos]
        self.center_camera(smooth=True)

    def update_reachable(self):
        if self.selected_unit:
            self.reachable = self.pathfinder.reachable(self.selected_unit.pos, self.selected_unit.ap, self.all_units())
        else:
            self.reachable = {}

    def check_objectives(self):
        if not any(u.alive for u in self.players):
            self.state = "defeat"
            return
        if self.map.terminal_positions and any(u.pos in self.map.terminal_positions for u in self.players if u.alive):
            self.terminal_used = True
        enemies_down = all(not e.alive for e in self.enemies)
        at_exit = self.map.exit_pos and any(u.alive and u.pos == self.map.exit_pos for u in self.players)
        terminal_ok = not self.map.terminal_positions or self.terminal_used
        if (at_exit and terminal_ok) or enemies_down:
            self.win_level()

    def win_level(self):
        self.state = "victory"
        stats = dict(self.stats)
        if self.level_index >= 0:
            self.save_manager.unlock_level(min(self.level_index + 1, len(LEVELS)))
            self.save_manager.record_result(self.level_name, stats)

    def center_camera(self, smooth=False):
        if not self.selected_unit:
            return
        tx = self.selected_unit.pixel_pos[0] - MAP_VIEW_WIDTH / 2
        ty = self.selected_unit.pixel_pos[1] - SCREEN_HEIGHT / 2
        max_x = max(0, self.map.width * TILE_SIZE - MAP_VIEW_WIDTH)
        max_y = max(0, self.map.height * TILE_SIZE - SCREEN_HEIGHT)
        tx = max(0, min(max_x, tx))
        ty = max(0, min(max_y, ty))
        if smooth:
            self.camera.x += (tx - self.camera.x) * 0.12
            self.camera.y += (ty - self.camera.y) * 0.12
        else:
            self.camera.x, self.camera.y = tx, ty

    def draw(self):
        if self.state == "menu":
            self.ui.draw_menu(self.screen, self.save_manager)
        else:
            self.draw_game()
            if self.state == "paused":
                self.ui.draw_overlay_message(self.screen, "Paused", ["ESC: resume", "Q: return to menu"])
            elif self.state == "victory":
                self.ui.draw_overlay_message(self.screen, "Mission Complete", self.result_lines())
            elif self.state == "defeat":
                self.ui.draw_overlay_message(self.screen, "Squad Lost", ["The building went quiet.", "ENTER: return to menu"])
        pygame.display.flip()

    def draw_game(self):
        self.screen.fill((7, 10, 18))
        self.map.draw(self.screen, self.camera, self.fog)
        self.draw_reachable()
        self.sound_system.draw(self.screen, self.camera)
        for enemy in self.enemies:
            visible = enemy.alive and self.map.tile_at(*enemy.pos).visible
            heard = enemy.pos in self.heard_enemy_marks
            enemy.draw(self.screen, self.camera, visible=visible, heard=heard)
        for player in self.players:
            player.draw(self.screen, self.camera, selected=player == self.selected_unit)
        self.particles.draw(self.screen, self.camera)
        self.ui.draw_hud(self.screen, self)

    def draw_reachable(self):
        if not self.reachable:
            return
        overlay = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        overlay.fill((58, 255, 155, 45))
        for x, y in self.reachable:
            rect = pygame.Rect(x * TILE_SIZE - self.camera.x, y * TILE_SIZE - self.camera.y, TILE_SIZE, TILE_SIZE)
            self.screen.blit(overlay, rect)
        if self.map.exit_pos:
            ex, ey = self.map.exit_pos
            rect = pygame.Rect(ex * TILE_SIZE - self.camera.x + 8, ey * TILE_SIZE - self.camera.y + 8, TILE_SIZE - 16, TILE_SIZE - 16)
            pygame.draw.rect(self.screen, YELLOW, rect, 2, border_radius=4)

    def result_lines(self):
        return [
            f"Level: {self.level_name}",
            f"Turns: {self.stats['turns']}",
            f"Kills: {self.stats['kills']}",
            f"Scans used: {self.stats['scans']}",
            "ENTER: return to menu",
        ]
