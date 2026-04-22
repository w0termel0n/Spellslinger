from dataclasses import dataclass, field
from typing import Dict
import time

@dataclass
class Spell:
    '''
    Manages the names and attributes of spells for SpellSlinger

    Data Fields:
        _timestamp - timestamp of spell cast
        _dmg (int) - damage value of spell
        _mana_cost - mana cost of spell
        _effects - tracks all % changes for applications of special effects
    '''
    timestamp: float = field(default_factory=time.time)
    dmg: int = 0
    mana_cost: int = 0
    effects: Dict[str, int] = field(default_factory=dict)
    delivery: str = "instant"
    projectile_img: str = None
    leech: bool = False

    @classmethod
    def from_name(cls, name: str, spell_data: dict):
        if name not in spell_data:
            raise ValueError(f"Spell '{name}' does not exist.")

        data = spell_data[name]

        return cls(
            dmg=data["dmg"],
            mana_cost=data["mana_cost"],
            effects=data["effects"].copy(),
            delivery=data.get("delivery", "instant"),
            projectile_img=data.get("projectile_img"),
            leech=data.get("leech", False)
        )
