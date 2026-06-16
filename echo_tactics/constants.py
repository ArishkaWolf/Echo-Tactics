import pygame

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
TILE_SIZE = 40
FPS = 60
SIDEBAR_WIDTH = 300

MAP_VIEW_WIDTH = SCREEN_WIDTH - SIDEBAR_WIDTH

BG = (7, 10, 18)
PANEL = (16, 23, 35)
PANEL_2 = (25, 35, 52)
CYAN = (47, 230, 255)
BLUE = (65, 128, 255)
GREEN = (58, 255, 155)
YELLOW = (255, 216, 88)
ORANGE = (255, 142, 63)
RED = (255, 74, 105)
MAGENTA = (230, 73, 255)
WHITE = (230, 241, 255)
MUTED = (124, 147, 170)
BLACK = (0, 0, 0)

TILE_COLORS = {
    "floor": (18, 27, 42),
    "wall": (43, 50, 70),
    "door": (112, 83, 46),
    "window": (39, 103, 122),
    "cover": (56, 68, 82),
    "terminal": (34, 89, 73),
    "exit": (35, 90, 65),
}

MOVE_SOUND = 4
WAIT_SOUND = 1
ATTACK_SOUND = 9
DOOR_SOUND = 6
SCAN_SOUND = 12

PLAYER_START_AP = 6
ENEMY_START_AP = 5

pygame.font.init()
