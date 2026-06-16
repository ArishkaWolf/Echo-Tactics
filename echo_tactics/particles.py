import random

import pygame

from .constants import ORANGE, TILE_SIZE, YELLOW


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def spawn_shot(self, start, end):
        sx, sy = start[0] * TILE_SIZE + TILE_SIZE // 2, start[1] * TILE_SIZE + TILE_SIZE // 2
        ex, ey = end[0] * TILE_SIZE + TILE_SIZE // 2, end[1] * TILE_SIZE + TILE_SIZE // 2
        for _ in range(14):
            t = random.random()
            x = sx + (ex - sx) * t
            y = sy + (ey - sy) * t
            self.particles.append([x, y, random.uniform(-30, 30), random.uniform(-30, 30), 0.35, random.choice([YELLOW, ORANGE])])

    def update(self, dt):
        for p in self.particles:
            p[0] += p[2] * dt
            p[1] += p[3] * dt
            p[4] -= dt
        self.particles = [p for p in self.particles if p[4] > 0]

    def draw(self, surface, camera):
        for x, y, _, _, life, color in self.particles:
            alpha = int(255 * max(0, life / 0.35))
            overlay = pygame.Surface((8, 8), pygame.SRCALPHA)
            pygame.draw.circle(overlay, (*color, alpha), (4, 4), 3)
            surface.blit(overlay, (x - camera.x - 4, y - camera.y - 4))
