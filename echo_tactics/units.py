import math

import pygame

from .constants import (
    ATTACK_SOUND,
    BLUE,
    CYAN,
    ENEMY_START_AP,
    GREEN,
    ORANGE,
    PLAYER_START_AP,
    RED,
    TILE_SIZE,
    WHITE,
    YELLOW,
)


class Unit:
    def __init__(self, x, y, name, team):
        self.pos = (x, y)
        self.name = name
        self.team = team
        self.hp = 10
        self.max_hp = 10
        self.ap = PLAYER_START_AP if team == "player" else ENEMY_START_AP
        self.max_ap = self.ap
        self.alive = True
        self.alert_target = None
        self.last_seen_player = None
        self.pixel_pos = [x * TILE_SIZE + TILE_SIZE // 2, y * TILE_SIZE + TILE_SIZE // 2]
        self.move_queue = []

    def reset_ap(self):
        self.ap = self.max_ap

    def distance_to(self, other):
        target = other.pos if isinstance(other, Unit) else other
        return math.dist(self.pos, target)

    def can_attack(self, other, fog=None):
        return self.alive and other.alive and self.distance_to(other) <= 5 and (fog is None or fog.has_line_of_sight(self.pos, other.pos))

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0
            self.alive = False

    def move_along(self, path, cost):
        if len(path) <= 1:
            return
        self.pos = path[-1]
        self.ap -= cost
        self.move_queue = [((x * TILE_SIZE + TILE_SIZE // 2), (y * TILE_SIZE + TILE_SIZE // 2)) for x, y in path[1:]]

    def update_animation(self, dt):
        if not self.move_queue:
            self.pixel_pos[0] = self.pos[0] * TILE_SIZE + TILE_SIZE // 2
            self.pixel_pos[1] = self.pos[1] * TILE_SIZE + TILE_SIZE // 2
            return
        tx, ty = self.move_queue[0]
        dx = tx - self.pixel_pos[0]
        dy = ty - self.pixel_pos[1]
        dist = math.hypot(dx, dy)
        speed = 300 * dt
        if dist <= speed:
            self.pixel_pos = [tx, ty]
            self.move_queue.pop(0)
        else:
            self.pixel_pos[0] += dx / dist * speed
            self.pixel_pos[1] += dy / dist * speed

    def draw(self, surface, camera, visible=True, heard=False, selected=False):
        if not self.alive:
            return
        px = int(self.pixel_pos[0] - camera.x)
        py = int(self.pixel_pos[1] - camera.y)
        if heard and not visible:
            pygame.draw.circle(surface, (255, 255, 255, 70), (px, py), 14, 1)
            pygame.draw.circle(surface, (255, 255, 255, 35), (px, py), 5)
            return
        color = BLUE if self.team == "player" else RED
        outline = CYAN if selected else WHITE
        pygame.draw.circle(surface, color, (px, py), 14)
        pygame.draw.circle(surface, outline, (px, py), 15, 2)
        if self.team == "player":
            pygame.draw.polygon(surface, GREEN, [(px, py - 19), (px - 6, py - 8), (px + 6, py - 8)])
        else:
            pygame.draw.polygon(surface, ORANGE, [(px, py + 18), (px - 7, py + 7), (px + 7, py + 7)])
        hp_w = 24
        pygame.draw.rect(surface, (40, 8, 14), (px - 12, py + 18, hp_w, 4))
        pygame.draw.rect(surface, GREEN if self.hp > 4 else YELLOW, (px - 12, py + 18, int(hp_w * self.hp / self.max_hp), 4))


class PlayerUnit(Unit):
    def __init__(self, x, y, name):
        super().__init__(x, y, name, "player")

    def attack(self, enemy, sound_system, particles):
        if self.ap < 2:
            return False
        self.ap -= 2
        enemy.take_damage(4)
        sound_system.add_event(*self.pos, ATTACK_SOUND, f"{self.name} fired", "player")
        particles.spawn_shot(self.pos, enemy.pos)
        return True


class EnemyUnit(Unit):
    def __init__(self, x, y, name):
        super().__init__(x, y, name, "enemy")
        self.patrol_origin = (x, y)
        self.patrol_index = 0
        self.patrol_points = [(x, y), (x + 2, y), (x + 2, y + 2), (x, y + 2)]

    def take_turn(self, game):
        if not self.alive:
            return
        self.reset_ap()
        visible_players = [u for u in game.players if u.alive and game.fog.has_line_of_sight(self.pos, u.pos) and self.distance_to(u) <= 6]
        if visible_players:
            target = min(visible_players, key=lambda u: self.distance_to(u))
            self.last_seen_player = target.pos
            self._engage(target, game)
            return
        heard = game.sound_system.latest_audible_for(self.pos, game.map, min_strength=2.0)
        if heard and heard.team == "player":
            self.alert_target = (heard.x, heard.y)
        if self.alert_target:
            self._move_toward(self.alert_target, game, cautious=True)
            if self.pos == self.alert_target:
                self.alert_target = None
            return
        self._patrol(game)

    def _engage(self, target, game):
        if self.can_attack(target, game.fog) and self.ap >= 2:
            defense = game.map.tile_at(*target.pos).defense_bonus
            target.take_damage(max(1, 3 - defense))
            self.ap -= 2
            game.sound_system.add_event(*self.pos, ATTACK_SOUND, f"{self.name} fired", "enemy")
            game.particles.spawn_shot(self.pos, target.pos)
            return
        desired = target.pos
        if self.distance_to(target) < 3:
            desired = self._best_cover_or_retreat(game, target)
        self._move_toward(desired, game, cautious=False)

    def _move_toward(self, target, game, cautious=False):
        path = game.pathfinder.find_path(self.pos, target, units=game.all_units())
        if len(path) > 1:
            steps = min(self.ap, 2 if cautious else 4, len(path) - 1)
            self.move_along(path[: steps + 1], steps)

    def _patrol(self, game):
        target = self.patrol_points[self.patrol_index % len(self.patrol_points)]
        if not game.map.in_bounds(*target) or not game.map.is_walkable(*target):
            target = self.patrol_origin
        if self.pos == target:
            self.patrol_index += 1
            target = self.patrol_points[self.patrol_index % len(self.patrol_points)]
        self._move_toward(target, game, cautious=True)

    def _best_cover_or_retreat(self, game, target):
        candidates = list(game.map.neighbors(*self.pos, units=game.all_units()))
        if not candidates:
            return self.pos
        candidates.sort(key=lambda p: (game.map.tile_at(*p).defense_bonus, self.distance_to(target)), reverse=True)
        return candidates[0]
