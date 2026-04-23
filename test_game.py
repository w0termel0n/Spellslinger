import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

import unittest
from unittest.mock import MagicMock
from spell import Spell
from spell_list import SPELL_LIST
from run_game import deal_damage, process_effects, cast_spell, clamp, regen_mana
import pygame
pygame.init()
pygame.display.set_mode((1, 1))
def make_state():
    return {"score": 0, "spell_count": 0, "last_pos": None, "stroke_points": []}

class FakeEntity:
    def __init__(self, health=200, mana=100):
        self.health = health
        self.mana = mana
        self.max_health = 200
        self.max_mana = 100
        self.effects = {}
        self.last_mana_regen = 0
        
        # fake rect for projectile positioning
        self.rect = MagicMock()
        self.rect.midright = (0, 0)
        self.rect.midleft = (0, 0)
    
    def spend_mana(self, amount):
        if self.mana >= amount:
            self.mana -= amount
            return True
        return False
    
    def __str__(self):
        return "Entity"

def make_entity(health=200, mana=100):
    return FakeEntity(health, mana)

class TestDealDamage(unittest.TestCase):
    def test_basic_damage(self):
        caster, target, state = make_entity(), make_entity(), make_state()
        deal_damage(caster, target, 50, state)
        self.assertEqual(target.health, 150)

    def test_shield_halves_damage(self):
        caster, target, state = make_entity(), make_entity(), make_state()
        target.effects = {"shield": {"uses": 1}}
        deal_damage(caster, target, 50, state)
        self.assertEqual(target.health, 175)

    def test_damage_cannot_exceed_max_health(self):
        caster, target, state = make_entity(), make_entity(), make_state()
        deal_damage(caster, target, 999, state)
        self.assertEqual(target.health, 0)

    def test_score_increases_with_damage_dealt(self):
        from run_game import Player, Enemy
        caster = make_entity()
        caster.__class__ = Player
        target = make_entity()
        state = make_state()
        deal_damage(caster, target, 50, state)
        self.assertEqual(state["score"], 50)

    def test_score_decreases_with_damage_taken(self):
        from run_game import Player
        caster = make_entity()
        target = make_entity()
        target.__class__ = Player
        state = make_state()
        deal_damage(caster, target, 50, state)
        self.assertEqual(state["score"], 0)

class TestProcessEffects(unittest.TestCase):
    def test_effect_removed_when_duration_expires(self):
        entity = make_entity()
        entity.effects = {"freezing": {"duration": 0.1, "slow": 0.5}}
        state = make_state()
        process_effects(entity, 1.0, state)  # 1 second passes
        self.assertNotIn("freezing", entity.effects)

    def test_effect_remains_when_duration_not_expired(self):
        entity = make_entity()
        entity.effects = {"freezing": {"duration": 5.0, "slow": 0.5}}
        state = make_state()
        process_effects(entity, 1.0, state)
        self.assertIn("freezing", entity.effects)

class TestSpendMana(unittest.TestCase):
    def test_spend_mana_succeeds_when_enough(self):
        from run_game import Player
        p = Player.__new__(Player)
        p.mana = 100
        result = p.spend_mana(30)
        self.assertTrue(result)
        self.assertEqual(p.mana, 70)

    def test_spend_mana_fails_when_not_enough(self):
        from run_game import Player
        p = Player.__new__(Player)
        p.mana = 10
        result = p.spend_mana(30)
        self.assertFalse(result)
        self.assertEqual(p.mana, 10)

class TestClamp(unittest.TestCase):
    def test_clamp_within_range(self):
        self.assertEqual(clamp(50, 0, 100), 50)

    def test_clamp_below_minimum(self):
        self.assertEqual(clamp(-10, 0, 100), 0)

    def test_clamp_above_maximum(self):
        self.assertEqual(clamp(150, 0, 100), 100)

    def test_clamp_at_minimum(self):
        self.assertEqual(clamp(0, 0, 100), 0)

    def test_clamp_at_maximum(self):
        self.assertEqual(clamp(100, 0, 100), 100)


class TestRegenMana(unittest.TestCase):
    def test_mana_regens_after_2_seconds(self):
        entity = make_entity(mana=50)
        entity.last_mana_regen = pygame.time.get_ticks() - 2001
        entity.effects = {}
        regen_mana(entity)
        self.assertEqual(entity.mana, 55)

    def test_mana_does_not_regen_before_2_seconds(self):
        entity = make_entity(mana=50)
        entity.last_mana_regen = pygame.time.get_ticks() - 500
        entity.effects = {}
        regen_mana(entity)
        self.assertEqual(entity.mana, 50)

    def test_mana_does_not_exceed_maximum(self):
        entity = make_entity(mana=98)
        entity.last_mana_regen = pygame.time.get_ticks() - 2001
        entity.effects = {}
        regen_mana(entity)
        self.assertEqual(entity.mana, 100)

    def test_freezing_slows_regen(self):
        entity = make_entity(mana=50)
        entity.last_mana_regen = pygame.time.get_ticks() - 2001
        entity.effects = {"freezing": {"duration": 5.0, "slow": 0.5}}
        regen_mana(entity)
        self.assertEqual(entity.mana, 52.5)  # 5 * (1 - 0.5) = 2.5 regen

    def test_blitz_increases_regen(self):
        entity = make_entity(mana=50)
        entity.last_mana_regen = pygame.time.get_ticks() - 2001
        entity.effects = {"blitz": {"duration": 5.0, "bonus_regen": 5}}
        regen_mana(entity)
        self.assertEqual(entity.mana, 60)  # 5 + 5 bonus = 10 regen

    def test_freezing_and_blitz_together(self):
        entity = make_entity(mana=50)
        entity.last_mana_regen = pygame.time.get_ticks() - 2001
        entity.effects = {
            "freezing": {"duration": 5.0, "slow": 0.5},
            "blitz": {"duration": 5.0, "bonus_regen": 5}
        }
        regen_mana(entity)
        self.assertEqual(entity.mana, 57.5)  # 5 * 0.5 + 5 bonus = 7.5 regen

class TestCastSpell(unittest.TestCase):

    def test_spell_not_cast_without_enough_mana(self):
        caster = make_entity(mana=0)
        target = make_entity()
        projectiles = []
        state = make_state()
        cast_spell("fireball", caster, target, projectiles, state)
        # nothing should have been added to projectiles
        self.assertEqual(len(projectiles), 0)
        # mana should be unchanged
        self.assertEqual(caster.mana, 0)

    def test_projectile_spell_adds_to_projectiles(self):
        caster = make_entity(mana=100)
        target = make_entity()
        projectiles = []
        state = make_state()
        cast_spell("fireball", caster, target, projectiles, state)
        self.assertEqual(len(projectiles), 1)

    def test_curse_blocks_spell(self):
        caster = make_entity(mana=100)
        caster.effects = {"curse": {"duration": 5.0, "blocked_spell": "fireball"}}
        target = make_entity()
        projectiles = []
        state = make_state()
        cast_spell("fireball", caster, target, projectiles, state)
        self.assertEqual(len(projectiles), 0)

    def test_curse_does_not_block_other_spells(self):
        caster = make_entity(mana=100)
        caster.effects = {"curse": {"duration": 5.0, "blocked_spell": "fireball"}}
        target = make_entity()
        projectiles = []
        state = make_state()
        cast_spell("frostbite", caster, target, projectiles, state)
        self.assertEqual(len(projectiles), 1)

    def test_counterspell_removes_projectile(self):
        caster = make_entity(mana=100)
        target = make_entity()
        projectiles = []
        state = make_state()
        # First launch a fireball at caster
        cast_spell("fireball", target, caster, projectiles, state)
        self.assertEqual(len(projectiles), 1)
        # Now counterspell it
        cast_spell("counterspell", caster, target, projectiles, state)
        self.assertEqual(len(projectiles), 0)

if __name__ == "__main__":
    unittest.main()