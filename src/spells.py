from dataclasses import dataclass, field
from typing import Dict

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
    timestamp: float = 0
    dmg: int = 0
    mana_cost: int = 0
    effects: Dict[str, int] = field(default_factory=lambda: {
        
    })

    
    #def apply_effect(self, effect_name: str, value: int):
    #    if effect_name in self.effects:
    #        self.effects[effect_name] += value
    #    else:
    #        raise ValueError(f"Unknown effect: {effect_name}")
