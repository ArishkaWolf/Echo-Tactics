class TurnManager:
    def __init__(self):
        self.phase = "player"
        self.turn = 1
        self.selected_index = 0

    def current_unit(self, players):
        alive = [u for u in players if u.alive]
        if not alive:
            return None
        self.selected_index %= len(alive)
        return alive[self.selected_index]

    def next_unit(self, players):
        alive = [u for u in players if u.alive]
        if alive:
            self.selected_index = (self.selected_index + 1) % len(alive)

    def start_player_turn(self, players):
        self.phase = "player"
        self.turn += 1
        for unit in players:
            if unit.alive:
                unit.reset_ap()

    def start_enemy_turn(self):
        self.phase = "enemy"
