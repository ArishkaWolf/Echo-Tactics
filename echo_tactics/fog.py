import math

import pygame

from .constants import BLACK, TILE_SIZE


class FogOfWar:
    def __init__(self, tactical_map):
        self.map = tactical_map
        self.sight_radius = 6

    def update(self, player_units):
        for row in self.map.tiles:
            for tile in row:
                tile.visible = False
        for unit in player_units:
            if not unit.alive:
                continue
            ux, uy = unit.pos
            for y in range(uy - self.sight_radius, uy + self.sight_radius + 1):
                for x in range(ux - self.sight_radius, ux + self.sight_radius + 1):
                    if not self.map.in_bounds(x, y):
                        continue
                    if math.dist((ux, uy), (x, y)) <= self.sight_radius and self.has_line_of_sight((ux, uy), (x, y)):
                        tile = self.map.tile_at(x, y)
                        tile.visible = True
                        tile.seen = True

    def has_line_of_sight(self, start, end):
        for x, y in self._line(start, end)[1:-1]:
            tile = self.map.tile_at(x, y)
            if tile and tile.blocks_sight:
                return False
        return True

    def draw_tile_overlay(self, surface, rect, seen):
        overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 130 if seen else 220))
        surface.blit(overlay, rect)

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
