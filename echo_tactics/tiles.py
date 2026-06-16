from dataclasses import dataclass


@dataclass
class Tile:
    x: int
    y: int
    kind: str
    open: bool = False
    seen: bool = False
    visible: bool = False

    @property
    def blocks_movement(self):
        return self.kind == "wall" or (self.kind == "door" and not self.open)

    @property
    def blocks_sight(self):
        return self.kind == "wall" or (self.kind == "door" and not self.open)

    @property
    def sound_damping(self):
        if self.kind == "wall":
            return 4.0
        if self.kind == "door" and not self.open:
            return 2.5
        if self.kind == "window":
            return 1.4
        if self.kind == "cover":
            return 1.2
        return 1.0

    @property
    def defense_bonus(self):
        return 2 if self.kind == "cover" else 0
