from dataclasses import dataclass, field

@dataclass
class Level:
    lower_map: list
    upper_map: list
    player_start: dict
    sky_mode: bool = False
    time_limit: float = 90.0
    number: int = 1
    props: list = field(default_factory=list)
    interactables: list = field(default_factory=list)
    traps: list = field(default_factory=list)
    battery_traps: list = field(default_factory=list)
    floor_overrides: dict = field(default_factory=dict)
    music: str = ""
    music_loop: bool = True
