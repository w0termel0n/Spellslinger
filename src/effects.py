from spell_list import SPELL_LIST
import random

def effect_blindness(caster, target):
    target.effects["blind"] = {
        "duration": 5.0
    }

def effect_blitz(caster, target):
    caster.effects["blitz"] = {
        "duration": 5.0,
        "bonus_regen": 10
    }

#def effect_counter(target):

def effect_curse(caster, target):
    target.effects["curse"] = {
    "duration": 5.0,
    "blocked_spell": random.choice(list(SPELL_LIST.keys()))
    }

def effect_burning(caster, target):
    target.effects["burning"] = {
        "duration": 5.0,
        "tick_damage": 2,
        "source": caster,
    }

def effect_freezing(caster, target):
    target.effects["freezing"] = {
        "duration": 5.0,
        "slow": 0.5
    }

def effect_glaciate(caster, target):
    caster.effects["glaciate"] = {
        "duration": 5.0,
        "bonus_chance": 0.25
    }

def effect_kindling(caster, target):
    caster.effects["kindling"] = {
        "duration": 5.0,
        "bonus_chance": 0.25
    }

def effect_leech(caster, target):
    caster.effects["leech"] = {
        "duration": 5.0,
        "ratio": 1.0
    }

def effect_roulette(caster, target):
    caster.effects["blitz"] = {
        "duration": 5.0,
        "bonus_regen": 5
    }
    
    caster.effects["burning"] = {
        "duration": 5.0,
        "tick_damage": 2
    }

    caster.effects["curse"] = {
    "duration": 5.0,
    "blocked_spell": random.choice(list(SPELL_LIST.keys()))
    } 

    caster.effects["freezing"] = {
        "duration": 5.0,
        "slow": 0.5
    }

    caster.effects["glaciate"] = {
        "duration": 5.0,
        "bonus_chance": 0.25
    }

    caster.effects["kindling"] = {
        "duration": 5.0,
        "bonus_chance": 0.25
    }

    caster.effects["shield"] = {
        "duration": 5,
        "protection": 1
    }
    
    target.effects["blitz"] = {
        "duration": 5.0,
        "bonus_regen": 5
    }
    
    target.effects["burning"] = {
        "duration": 5.0,
        "tick_damage": 2
    }

    target.effects["curse"] = {
        "duration": 5.0,
        "blocked_spell": random.choice(list(SPELL_LIST.keys()))
    }

    target.effects["freezing"] = {
        "duration": 5.0,
        "slow": 0.5
    }

    target.effects["glaciate"] = {
        "duration": 5.0,
        "bonus_chance": 0.25
    }

    target.effects["kindling"] = {
        "duration": 5.0,
        "bonus_chance": 0.25
    }

    target.effects["shield"] = {
        "duration": 5,
        "protection": 1
    }

def effect_shield(caster, target):
    caster.effects["shield"] = {
        "duration": 5,
        "protection": 1
    }



EFFECTS = {
    "blind": effect_blindness,
    "blitz": effect_blitz,
    "burning": effect_burning,
    "curse": effect_curse,
    "freezing": effect_freezing,
    "glaciate": effect_glaciate,
    "kindling": effect_kindling,
    "leech": effect_leech,
    "roulette": effect_roulette,
    "shield": effect_shield,
}