import random

import pygame

from .constants import TILE_COLORS, TILE_SIZE, CYAN, GREEN, MUTED, ORANGE, YELLOW
from .levels import RANDOM_HEIGHT, RANDOM_WIDTH
from .tiles import Tile


CHAR_TO_TILE = {
    "#": "wall",
    ".": "floor",
    "P": "floor",
    "E": "floor",
    "D": "door",
    "W": "window",
    "C": "cover",
    "T": "terminal",
    "X": "exit",
}


class TacticalMap:
    def __init__(self, rows):
        self.rows = rows
        self.width = max(len(row) for row in rows)
        self.height = len(rows)
        self.tiles = []
        self.player_starts = []
        self.enemy_starts = []
        self.terminal_positions = []
        self.exit_pos = None
        self._parse()

    def _parse(self):
        for y, row in enumerate(self.rows):
            tile_row = []
            for x in range(self.width):
                char = row[x] if x < len(row) else "#"
                kind = CHAR_TO_TILE.get(char, "floor")
                tile_row.append(Tile(x, y, kind))
                if char == "P":
                    self.player_starts.append((x, y))
                elif char == "E":
                    self.enemy_starts.append((x, y))
                elif char == "T":
                    self.terminal_positions.append((x, y))
                elif char == "X":
                    self.exit_pos = (x, y)
            self.tiles.append(tile_row)

    @classmethod
    def random_mission(cls):
        grid = [["#" for _ in range(RANDOM_WIDTH)] for _ in range(RANDOM_HEIGHT)]
        rooms = []
        for _ in range(10):
            w, h = random.randint(4, 8), random.randint(3, 6)
            x = random.randint(1, RANDOM_WIDTH - w - 2)
            y = random.randint(1, RANDOM_HEIGHT - h - 2)
            rooms.append((x, y, w, h))
            for yy in range(y, y + h):
                for xx in range(x, x + w):
                    grid[yy][xx] = "."
        for a, b in zip(rooms, rooms[1:]):
            ax, ay = a[0] + a[2] // 2, a[1] + a[3] // 2
            bx, by = b[0] + b[2] // 2, b[1] + b[3] // 2
            for xx in range(min(ax, bx), max(ax, bx) + 1):
                grid[ay][xx] = "."
            for yy in range(min(ay, by), max(ay, by) + 1):
                grid[yy][bx] = "."
        for x, y, w, h in rooms[::2]:
            grid[y + h // 2][x + w - 1] = "D"
            grid[y + 1][x + 1] = "C"
        starts = rooms[0]
        exit_room = rooms[-1]
        for i in range(3):
            grid[starts[1] + 1 + i % max(1, starts[3] - 2)][starts[0] + 1] = "P"
        for room in rooms[3::2]:
            grid[room[1] + room[3] // 2][room[0] + room[2] // 2] = "E"
        grid[exit_room[1] + exit_room[3] // 2][exit_room[0] + exit_room[2] - 2] = "X"
        grid[rooms[len(rooms) // 2][1] + 1][rooms[len(rooms) // 2][0] + 1] = "T"
        return cls(["".join(row) for row in grid])

    def in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def tile_at(self, x, y):
        if not self.in_bounds(x, y):
            return None
        return self.tiles[y][x]

    def is_walkable(self, x, y, units=None):
        tile = self.tile_at(x, y)
        if not tile or tile.blocks_movement:
            return False
        if units:
            return all(not u.alive or u.pos != (x, y) for u in units)
        return True

    def neighbors(self, x, y, units=None, ignore_units=False):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if self.is_walkable(nx, ny, None if ignore_units else units):
                yield nx, ny

    def open_door_at(self, x, y):
        tile = self.tile_at(x, y)
        if tile and tile.kind == "door":
            tile.open = True
            return True
        return False

    def draw(self, surface, camera, fog, debug_visible=False):
        for y, row in enumerate(self.tiles):
            for x, tile in enumerate(row):
                rect = pygame.Rect(x * TILE_SIZE - camera.x, y * TILE_SIZE - camera.y, TILE_SIZE, TILE_SIZE)
                if not surface.get_rect().colliderect(rect):
                    continue
                visible = tile.visible or debug_visible
                seen = tile.seen or visible
                color = TILE_COLORS[tile.kind] if seen else (5, 8, 13)
                if not visible and seen:
                    color = tuple(max(0, c // 3) for c in color)
                pygame.draw.rect(surface, color, rect)
                pygame.draw.rect(surface, (23, 42, 62), rect, 1)
                if seen:
                    self._draw_detail(surface, rect, tile, visible)
                if fog and not visible:
                    fog.draw_tile_overlay(surface, rect, seen)

    def _draw_detail(self, surface, rect, tile, visible):
        alpha = 255 if visible else 120
        if tile.kind == "door":
            color = GREEN if tile.open else ORANGE
            pygame.draw.line(surface, color, rect.midleft, rect.midright, 4)
        elif tile.kind == "window":
            pygame.draw.line(surface, CYAN, rect.topleft, rect.bottomright, 2)
            pygame.draw.line(surface, CYAN, rect.topright, rect.bottomleft, 2)
        elif tile.kind == "cover":
            pygame.draw.rect(surface, MUTED, rect.inflate(-10, -18), border_radius=3)
        elif tile.kind == "terminal":
            pygame.draw.rect(surface, GREEN, rect.inflate(-14, -12), 2, border_radius=4)
            pygame.draw.circle(surface, GREEN, rect.center, 3)
        elif tile.kind == "exit":
            pygame.draw.rect(surface, YELLOW, rect.inflate(-8, -8), 2, border_radius=4)
            pygame.draw.polygon(surface, YELLOW, [(rect.centerx + 8, rect.centery), (rect.centerx - 4, rect.centery - 8), (rect.centerx - 4, rect.centery + 8)])
