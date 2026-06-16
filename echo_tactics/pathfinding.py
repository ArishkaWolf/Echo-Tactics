from collections import deque


class PathFinder:
    def __init__(self, tactical_map):
        self.map = tactical_map

    def find_path(self, start, goal, units=None, ignore_goal_unit=True):
        if start == goal:
            return [start]
        queue = deque([start])
        came_from = {start: None}
        while queue:
            current = queue.popleft()
            for nxt in self.map.neighbors(*current, units=units):
                if ignore_goal_unit and nxt == goal and self.map.tile_at(*nxt) and not self.map.tile_at(*nxt).blocks_movement:
                    pass
                if nxt in came_from:
                    continue
                came_from[nxt] = current
                if nxt == goal:
                    return self._reconstruct(came_from, goal)
                queue.append(nxt)
        return []

    def reachable(self, start, ap, units=None):
        queue = deque([(start, 0)])
        costs = {start: 0}
        while queue:
            current, cost = queue.popleft()
            if cost >= ap:
                continue
            for nxt in self.map.neighbors(*current, units=units):
                new_cost = cost + 1
                if new_cost <= ap and new_cost < costs.get(nxt, 999):
                    costs[nxt] = new_cost
                    queue.append((nxt, new_cost))
        return costs

    def _reconstruct(self, came_from, goal):
        path = [goal]
        while came_from[path[-1]] is not None:
            path.append(came_from[path[-1]])
        path.reverse()
        return path
