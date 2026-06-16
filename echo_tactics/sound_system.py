import math
from dataclasses import dataclass

import pygame

from .constants import CYAN, MAGENTA, TILE_SIZE


@dataclass
class SoundEvent:
    x: int
    y: int
    strength: float
    label: str
    team: str
    age: float = 0.0
    duration: float = 1.8

    @property
    def radius(self):
        return min(self.strength * TILE_SIZE, self.age / self.duration * self.strength * TILE_SIZE * 1.4)

    @property
    def alive(self):
        return self.age < self.duration


class SoundSystem:
    def __init__(self):
        self.events = []
        self.log = []

    def add_event(self, x, y, strength, label, team):
        event = SoundEvent(x, y, strength, label, team)
        self.events.append(event)
        self.log.insert(0, f"{label}: sector {x},{y} intensity {strength}")
        self.log = self.log[:8]
        return event

    def update(self, dt):
        for event in self.events:
            event.age += dt
        self.events = [event for event in self.events if event.alive]

    def heard_strength(self, event, listener_pos, tactical_map):
        distance = math.dist((event.x, event.y), listener_pos)
        damping = 0.0
        for x, y in self._line((event.x, event.y), listener_pos):
            tile = tactical_map.tile_at(x, y)
            if tile:
                damping += tile.sound_damping - 1.0
        return event.strength - distance - damping

    def latest_audible_for(self, listener_pos, tactical_map, min_strength=1.0):
        audible = []
        for event in self.events:
            power = self.heard_strength(event, listener_pos, tactical_map)
            if power >= min_strength:
                audible.append((power, event))
        audible.sort(key=lambda item: item[0], reverse=True)
        return audible[0][1] if audible else None

    def draw(self, surface, camera):
        for event in self.events:
            center = (event.x * TILE_SIZE + TILE_SIZE // 2 - camera.x, event.y * TILE_SIZE + TILE_SIZE // 2 - camera.y)
            radius = max(2, int(event.radius))
            alpha = max(20, int(160 * (1 - event.age / event.duration)))
            color = CYAN if event.team == "player" else MAGENTA
            overlay = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(overlay, (*color, alpha), (radius + 2, radius + 2), radius, 2)
            pygame.draw.circle(overlay, (*color, alpha // 3), (radius + 2, radius + 2), max(2, radius // 3), 1)
            surface.blit(overlay, (center[0] - radius - 2, center[1] - radius - 2))

    def _line(self, start, end):
        x0, y0 = start
        x1, y1 = end
        points = []
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            points.append((x0, y0))
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy
        return points
