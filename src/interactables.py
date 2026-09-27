from . import config
from .utils import camera_space, has_line_of_sight

class InteractState:

    __slots__ = ("sprite", "solid", "sound")

    def __init__(self, sprite, solid=False, sound=None):
        self.sprite = sprite
        self.solid = solid
        self.sound = sound

class Interactable:

    def __init__(self, x, y, states, angle=0.0, width=1.0, interact_radius=None,
                 height=1.0, y_offset=0.0, cyclic=True, highlight_sprite=None,
                 block_radius=None, billboard=False):
        self.x = x
        self.y = y
        self.states = states
        self.state = 0

        self.block_radius = block_radius

        self.billboard = billboard
        self.angle = angle
        self.width = width
        self.interact_radius = (interact_radius if interact_radius is not None
                                else config.INTERACT_RADIUS)
        self.height = height
        self.y_offset = y_offset
        self.cyclic = cyclic

        self.highlight_sprite = highlight_sprite

    @property
    def current(self):
        return self.states[self.state]

    @property
    def sprite(self):
        return self.current.sprite

    @property
    def solid(self):
        return self.current.solid

    def use(self):
        if self.cyclic:
            self.state = (self.state + 1) % len(self.states)
        else:
            self.state = min(self.state + 1, len(self.states) - 1)
        return self.current

class ButtonLink:

    def __init__(self, button, doors, open_state=1,
                 locked_index=0, unlocked_index=1):
        self.button = button
        self.doors = list(doors)
        self.open_state = open_state
        self.locked_index = locked_index
        self.unlocked_index = unlocked_index

    def sync(self):
        if self.button.state == self.open_state:

            for door in self.doors:
                if door.state == self.locked_index:
                    door.state = self.unlocked_index
        else:

            for door in self.doors:
                door.state = self.locked_index

    def is_unlocked(self, door):
        return door.state != self.locked_index

def select_highlight(objects, px, py, pa, game_map):
    best = None
    best_key = None
    for obj in objects:
        dist, theta, forward = camera_space(px, py, pa, obj.x, obj.y)
        if forward <= config.SPRITE_NEAR_CLIP:
            continue
        if dist > obj.interact_radius:
            continue
        if abs(theta) > config.FOV:
            continue
        if not has_line_of_sight(game_map, px, py, obj.x, obj.y):
            continue

        key = (abs(theta), dist)
        if best is None or key < best_key:
            best = obj
            best_key = key
    return best
