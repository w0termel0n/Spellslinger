import pygame
import random
from spells import Spell
from spell_list import SPELL_LIST
import sys
from effects import EFFECTS

# Import pygame.locals for easier access to key coordinates
from pygame.locals import (
    K_EQUALS,
    K_MINUS,
    K_ESCAPE,
    K_c,
    KEYDOWN,
    MOUSEBUTTONUP,
    QUIT,
    K_BACKQUOTE,
    K_1,
    K_2,
    K_3,
    K_4,
    K_5,
    K_6,
    K_7,
    K_8,
    K_9,
    K_0,
    K_BACKSPACE,
)

# ---------------
# CONSTANTS
# ---------------
# Define constants for the screen width and height
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 700
CENTER_X = SCREEN_WIDTH // 2
CENTER_Y = SCREEN_HEIGHT // 2

# Define constants for canvas width, height, and placement
CANVAS_LENGTH = 230
CANVAS_X = (CENTER_X) - 282
CANVAS_Y = (SCREEN_HEIGHT-CANVAS_LENGTH) - 30

# Define constants for player stats
MAX_MANA = 100
MAX_HEALTH = 100

# Define constants for colors
WHITE = (255,255,255)
BLACK = (0,0,0)
GRAY = (120,120,120)
BLUE = (0,0,255)
RED = (255,0,0)

# Define constant for drawing
BRUSH_SIZE = 10

# Define constant for framerate
FPS = 165

# Create dictionary for image cache
IMAGE_CACHE = {}

def get_image(path, size=(88, 66)):
    """
    Retrieves the image of a spell projectile

    Args:
        path (string) - path of image location
        size (tuple[int, int]) - width and height of image

    Returns:
        IMAGE_CACHE[key] (pygame.Surface) - cache and scaled image
    """
    # Set key for the dictionary
    key = (path, size)

    # Check if image is already in cache
    if key not in IMAGE_CACHE:
        # Load the image as a pygame image
        img = pygame.image.load(path).convert_alpha()
        # Scale the image to the correct size
        img = pygame.transform.scale(img, size)
        # Store the image in the cache
        IMAGE_CACHE[key] = img

    # Return the image
    return IMAGE_CACHE[key]

# Define list of effect icons
EFFECT_ICONS = {
    "blitz": "assets/effects/blitz.png",
    "burning": "assets/effects/burning.png",
    "curse": "assets/effects/curse_pixel.png",
    "freezing": "assets/effects/freezing.png",
    "glaciate": "assets/effects/glaciate.png",
    "kindling": "assets/effects/kindling.png",
    "shield": "assets/effects/shield.png",
    "blind": "assets/effects/blind.png",
    "leech": "assets/effects/leech.png",
}

# Define buffs & debuffs for effect icons
BUFFS = {"blitz", "glaciate", "kindling", "shield"}
DEBUFFS = {"blind", "burning", "freezing", "curse"}

# Create dictionary for icon cache
ICON_CACHE = {}

def get_icon(path, size=(40, 40)):
    """
    Retrieves the path of an effect icon

    Args:
        path (string) - path of icon location
        size (tuple[int, int])- width and height of icon    
    
    Returns:
        ICON_CACHE[key] (pygame.Surface) - cache and scaled image of effect icon
    """
    # Check if icon is already in cache 
    if path not in ICON_CACHE:
        # Load the icon as pygame image
        img = pygame.image.load(path).convert_alpha()
        # Resize the icon
        img = pygame.transform.scale(img, size)
        # Store the icon into cahce
        ICON_CACHE[path] = img

    # Return the icon
    return ICON_CACHE[path]

# Define spell abbreviations for effects
SPELL_ABBREVIATIONS = {
    "blindness": "BL",
    "blitz": "BZ",
    "counterspell": "CS",
    "curse": "CR",
    "fireball": "FB",
    "frostbite": "FR",
    "glaciate": "GL",
    "kindling": "KD",
    "leech": "LE",
    "roulette": "RL",
    "shield": "SH",
    "spike": "SP",
}


# ---------------
# CLASSES
# ---------------
class Entity(pygame.sprite.Sprite):
    """
    Base class for game entities (players, enemies)

    Provides tracking for sprite, health, mana, and active effects

    Attributes:
        image (pygame.Surface) - sprite image
        rect (pygame.Rect) - surface containing sprite
        max_health (int) - maximum possible health
        health (int) - current health
        max_mana (int) - maximum possible mana
        mana (int) - current mana
        last_mana_regen (int) - timestamp of most recent mana value
        effects (dictionary) - active effects

    Methods:
        __init__() - initiales an Entity
        spend_mana() - determine if Entity has enough mana for a spell
        __str__() - return type of Class
    """
    def __init__(self, icon, position, max_health=100, max_mana=100):
        """
        Initializes an Entity

        Args:
            icon (str) - path to sprite image 
            position (tuple[int, int]) - x, y position of sprite 
            max_health (int) - maximum possible health
            max_mana (int) - maximum possible mana
        """
        super().__init__()
        self.image = pygame.image.load(icon).convert()
        self.image = pygame.transform.scale(self.image, (200, 250))

        self.rect = self.image.get_rect(topleft=position)

        # Core stats
        self.max_health = max_health
        self.health = max_health

        self.max_mana = max_mana
        self.mana = max_mana

        self.last_mana_regen = pygame.time.get_ticks()

        self.effects = {}

    def spend_mana(self, amount):
        """
        Determines if mana can be spent on spell

        Args:
            amount (int) - mana cost of spell

        Returns:
            bool - True if enough mana to cast, else False
        """
        if self.mana >= amount:
            self.mana -= amount
            return True
        return False
    
    def __str__(self):
        return "Entity"
    
class Player(Entity):
    """
    Subclass of Entity

    Methods:
        __init__() - initializes a Player
    """
    def __init__(self, icon, position):
        """
        Initializes a Player

        Args:
            icon (str) - path to sprite image 
            position (tuple[int, int]) - x, y position of sprite 
        """
        super().__init__(icon, position)


class Enemy(Entity):
    """
    Subclass of Entity

    Methods:
        __init__() - initializes an Enemy
    """

    def __init__(self, icon, position):
        """
        Initializes an Enemy

        Args:
            icon (str) - path to sprite image 
            position (tuple[int, int]) - x, y position of sprite 
        """
        super().__init__(icon, position)


class Projectile:
    """
    Class for spell projectiles

    Provides ability to track and draw projectiles of spells

    Attributes:
        caster (Entity) - entity who cast the spell
        target (Entity) - entity who will have spell applied to
        spell (Spell) - spell being cast
        duration (int) - flight time of spell

    Methods:
        __init__() - initiales a Projectile
        update() - tracks the position of the projectile
        projectile_draw() - draw the projectile in flight
    """
    def __init__(self, caster, target, spell, duration=2.0):
        """
        Initializes a Projectile

        Args:
            caster (Entity) - entity who cast the spell
            target (Entity) - entity who will have spell applied to
            spell (Spell) - spell being cast
            duration (int) - flight time of spell
        """
        self.caster = caster
        self.target = target
        self.spell = spell

        if spell.projectile_img:
            self.image = get_image(spell.projectile_img)
        else:
            self.image = None

        self.start_pos = caster.rect.midright
        self.end_pos = target.rect.midleft

        self.duration = duration
        self.elapsed = 0

        self.position = list(self.start_pos)

    def update(self, dt):
        """
        Tracks the position of a Projectile

        Args:
            dt (int) - time spent in flight

        Returns:
            bool - True if it's reached target, else False
        """
        
        self.elapsed += dt
        t = min(self.elapsed / self.duration, 1)

        # Linear interpolation (LERP)
        self.position[0] = self.start_pos[0] + (self.end_pos[0] - self.start_pos[0]) * t
        self.position[1] = self.start_pos[1] + (self.end_pos[1] - self.start_pos[1]) * t

        return t >= 1  # True when it reaches target

    def projectile_draw(self, screen):
        """
        Draws a Projectile in flight

        Args:
            screen (pygame.display) - screen to be drawn on
        """
        if self.image:
            rect = self.image.get_rect(center=(int(self.position[0]), int(self.position[1])))
            screen.blit(self.image, rect)

# ---------------
# UI FUNCTIONS
# ---------------
def clamp(value, min_val, max_val):
    """
    Set boundaries for a value

    Helper function for draw_value_bar

    Args:
        value (int) - value to be clamped
        min_val (int) - minimum possible value
        max_val (int) - maximum possible value

    Returns:
        If the value is less than the minimum, return the minimum
        If the value is greater than the maximum, return the maximum
        Else, return the value
    """
    return max(min_val, min(value, max_val))

def draw_value_bar(screen, color, current, max_value, x, y, length, height):
    """
    Draws a visible bar to track health and mana

    Args:
        screen (pygame.display) - screen to be drawn on
        color (string) - "mana" for BLUE or "health" for RED
        current (int) - current value of health or mana
        max_value (int) - maximum possible health or mana
        x (int) - x position of bar
        y (int) - y position of bar
        length (int) - length of bar
        height (int) - height of bar
    """
    current = clamp(current, 0, max_value)
    percentage = current / max_value

    pygame.draw.rect(screen, GRAY, (x, y, length, height))
    # Foreground, scaled by ratio
    if color == "mana":
        pygame.draw.rect(screen, BLUE, (x, y, int(length * percentage), height))
    elif color == "health":
        pygame.draw.rect(screen, RED, (x, y, int(length * percentage), height))
    # Border for clarity
    pygame.draw.rect(screen, BLACK, (x, y, length, height), 2)

def start_menu():
    """
    Draws the starting screen of the game
    """
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Spellslinger")

    pygame.font.init()
    font = pygame.font.SysFont("caveatregular", 30)
    title_font = pygame.font.SysFont("caveatregular", 80)

    running = True
    while running:

        screen.fill((60,25,60))
        mouse = pygame.mouse.get_pos()

        play_button = pygame.Rect(CENTER_X - 90, CENTER_Y - 50 // 2 - 20, 140, 50)
        quit_button = pygame.Rect(CENTER_X - 90, CENTER_Y - 50 // 2 + 60, 140, 50)

        pygame.draw.rect(screen, (170,170,170) if play_button.collidepoint(mouse) else (100,100,100), play_button)
        pygame.draw.rect(screen, (170,170,170) if quit_button.collidepoint(mouse) else (100,100,100), quit_button)

        title_text = title_font.render("Spellslinger", True, WHITE)
        play_text = font.render("Play", True, WHITE)
        quit_text = font.render("Quit", True, WHITE)

        screen.blit(title_text, (CENTER_X - 185, 100))
        screen.blit(play_text, (CENTER_X - 45, CENTER_Y - 50 // 2 - 15))
        screen.blit(quit_text, (CENTER_X - 45, CENTER_Y - 50 // 2 + 65))

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if play_button.collidepoint(mouse):
                    run()
                    return
                if quit_button.collidepoint(mouse):
                    running = False

        pygame.display.update()
    
    pygame.quit()
    sys.exit()

def abbreviate_spell(name):
    """
    Abbreviates the name of a spell

    Helper function to draw_effect_row

    Args:
        name (string) - name of spell to be abbreviated
    
    Returns:
        First 3 letters of the spell, all capitalized
    """
    return SPELL_ABBREVIATIONS.get(name, name[:3].upper())

def draw_effect_row(screen, entity, effects, x, y, direction="up"):
    """
    Draws icons for spell effects in a row

    Args:
        screen (pygame.display) - screen to be drawn on
        entity (Entity) - entity affected by spell
        effects (dictionary) - list of effect name and properties
        x (int) - x position of effect icon
        y (int) - y position of effect icon
        direction (str) - determines above or below value bars
    """
    spacing = 36
    for i, effect in enumerate(effects):
        if effect not in EFFECT_ICONS:
            continue

        icon = get_icon(EFFECT_ICONS[effect])

        if direction == "up":
            pos_y = y - spacing
        else:
            pos_y = y + spacing

         # --- CURSE LABEL ---
        if effect == "curse":
            blocked = entity.effects["curse"].get("blocked_spell", "")
            label_text = abbreviate_spell(blocked)

            font = pygame.font.SysFont("caveatregular", 30)
            label = font.render(label_text, True, GRAY)

            # center text under icon
            text_rect = label.get_rect(center=(x + 18   , y + 55))
            screen.blit(label, text_rect)

        screen.blit(icon, (x + i * spacing, pos_y))


# ---------------
# GAME FUNCTIONS
# ---------------
def init():
    """
    Initialzes the window for the game

    Returns:
        screen (pygame.display) - window the game will play in
        canvas (pygame.Surface) - drawable surface for spell runes
        player (Entity) - instance of the player
        sprites (pygame.sprite) - icons of player and enemy
        state (dictionary) - tracks # of spells and mouse position for canvas
        enemy (Entity) - instance of the enemy
        spellbook (pygame.image) - image of spellbook for UI
        projectiles (array) - array of active Projectiles
    """
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Spellslinger")

    spellbook = pygame.image.load("assets/Spellbook.png")
    spellbook = pygame.transform.scale(spellbook, (1250, 750))

    canvas = pygame.Surface((CANVAS_LENGTH, CANVAS_LENGTH))
    canvas.fill(WHITE)

    player = Player(
        "assets/Wizard-Left.png",
        ((SCREEN_WIDTH // 4) - 100, (SCREEN_HEIGHT - CANVAS_LENGTH) // 2 - 100),
    )

    enemy = Enemy(
        "assets/Wizard-Right.png",
        ((3 * SCREEN_WIDTH // 4) - 100, (SCREEN_HEIGHT - CANVAS_LENGTH) // 2 - 100),
    )

    sprites = pygame.sprite.Group(player, enemy)

    state = {
        "spell_count": 0,
        "last_pos": None,
    }

    projectiles = []

    return screen, canvas, player, sprites, state, enemy, spellbook, projectiles


def handle_events(state, canvas, player, enemy, projectiles):
    """
    Handles action events for the program

    Args:
        state (dictionary) - tracks # of spells and mouse position for canvas
        canvas (pygame.Surface) - drawable surface for spell runes
        player (Entity) - instance of the player
        enemy (Entity) - instance of the enemy
        projectiles (array) - array of active Projectiles

    Returns:
        bool - True until interuppted
    """
    for event in pygame.event.get():
        if event.type == QUIT:
            return False

        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                return False
            elif event.key == K_c:
                canvas.fill(WHITE)
            # Check for number keys (1-9) to cast corresponding spells
            elif event.key == K_BACKQUOTE:
                cast_spell("blindness", player, enemy, projectiles)
            elif event.key == K_1:
                cast_spell("blitz", player, enemy, projectiles)
            elif event.key == K_2:
                cast_spell("counterspell", enemy, player, projectiles)
            elif event.key == K_3:
                player.effects["curse"] = {
                "duration": 5.0,
                "blocked_spell": "fireball"
                }
                # cast_spell("curse", player, enemy, projectiles)
            elif event.key == K_4:
                cast_spell("fireball", player, enemy, projectiles)
            elif event.key == K_5:
                cast_spell("frostbite", player, enemy, projectiles)
            elif event.key == K_6:
                cast_spell("glaciate", player, enemy, projectiles)
            elif event.key == K_7:
                cast_spell("kindling", player, enemy, projectiles)
            elif event.key == K_8:
                cast_spell("leech", player, enemy, projectiles)
            elif event.key == K_9:
                cast_spell("roulette", player, enemy, projectiles)
            elif event.key == K_0:
                cast_spell("shield", player, enemy, projectiles)
            elif event.key == K_MINUS:
                cast_spell("spike", player, enemy, projectiles)
            elif event.key == K_EQUALS:
                enemy.effects["shield"] = { 
                    "duration": 9999, "uses": 1 
                } 
                print("Enemy given shield")
            elif event.key == K_BACKSPACE:
                player.health = clamp(player.health / 2, 0, player.max_health)

        elif event.type == MOUSEBUTTONUP and event.button == 1:
            mx, my = event.pos  # mouse position at release
            # Check if inside canvas bounds
            if (CANVAS_X <= mx < CANVAS_X + CANVAS_LENGTH and
                CANVAS_Y <= my < CANVAS_Y + CANVAS_LENGTH):
                
                save_canvas(canvas, state, player, enemy, projectiles)

    return True


def handle_drawing(canvas, state):
    """
    Handles drawing on the canvas

    Args:
        canvas (pygame.Surface) - drawable surface for spell runes
        state (dictionary) - tracks # of spells and mouse position for canvas
    """
    mx, my = pygame.mouse.get_pos()
    cx = mx - CANVAS_X
    cy = my - CANVAS_Y

    mouse_pressed = pygame.mouse.get_pressed()[0]

    if 0 <= cx < CANVAS_LENGTH and 0 <= cy < CANVAS_LENGTH:
        if mouse_pressed:
            if state["last_pos"]:
                pygame.draw.line(canvas, BLACK, state["last_pos"], (cx, cy), BRUSH_SIZE)

            pygame.draw.circle(canvas, BLACK, (cx, cy), BRUSH_SIZE // 2)
            state["last_pos"] = (cx, cy)
        else:
            state["last_pos"] = None
    else:
        state["last_pos"] = None


def save_canvas(canvas, state, player, enemy, projectiles):
    """
    Saves drawing on the canvas before reseting the canvas to blank

    Args:
        canvas (pygame.Surface) - drawable surface for spell runes
        state (dictionary) - tracks # of spells and mouse position for canvas
        player (Entity) - instance of the player
        enemy (Entity) - instance of the enemy
        projectiles (array) - array of active Projectiles
    """
    scaled = pygame.transform.scale(canvas, (280, 280))
    pygame.image.save(scaled, f"drawings/spell_{state['spell_count']}.png")
    state["spell_count"] += 1

    spell_name = recognize_spell()
    cast_spell(spell_name, player, enemy, projectiles)

    canvas.fill(WHITE)

def draw_player_canvas(screen, canvas, entity):
    """
    Draws the player's canvas on the screen

    Args:
        screen (pygame.display) - window the game will play in
        canvas (pygame.Surface) - drawable surface for spell runes
        entity (Entity) - entity who will see the canvas
    """
    if "blind" in entity.effects:
        black = pygame.Surface((CANVAS_LENGTH, CANVAS_LENGTH))
        black.fill(BLACK)
        screen.blit(black, (CANVAS_X, CANVAS_Y))
    else:
        screen.blit(canvas, (CANVAS_X, CANVAS_Y))

def draw(screen, canvas, player, sprites, enemy, spellbook, projectiles):
    """
    Draws the entire UI for the game

    Args:
        screen (pygame.display) - window the game will play in
        canvas (pygame.Surface) - drawable surface for spell runes
        player (Entity) - instance of the player
        sprites (pygame.sprite) - icons of player and enemy
        enemy (Entity) - instance of the enemy
        spellbook (pygame.image) - image of spellbook for UI
        projectiles (array) - array of active Projectiles
    """
    # Draw Background
    screen.fill(BLACK)

     # Draw Spellbook
    screen.blit(spellbook, (CENTER_X - 590, SCREEN_HEIGHT - 525))

    # Draw Canvas
    draw_player_canvas(screen, canvas, player)

    # Draw Player
    for entity in sprites:
        screen.blit(entity.image, entity.rect)

    # Draw Player Mana
    draw_value_bar(
        screen,
        "mana",
        player.mana,
        MAX_MANA,
        CENTER_X + 57,
        SCREEN_HEIGHT - 160,
        250,
        20,
    )

    # Draw Player Health
    draw_value_bar(
        screen,
        "health",
        player.health,
        MAX_HEALTH,
        CENTER_X + 57,
        SCREEN_HEIGHT - 140,
        250,
        20
    )

    player_buffs = [e for e in player.effects if e in BUFFS]
    player_debuffs = [e for e in player.effects if e in DEBUFFS]

    # Buffs ABOVE mana bar
    draw_effect_row(
        screen,
        player,
        player_buffs,
        CENTER_X + 57,
        SCREEN_HEIGHT - 160,
        direction="up"
    )

    # Debuffs BELOW health bar
    draw_effect_row(
        screen,
        player,
        player_debuffs,
        CENTER_X + 57,
        SCREEN_HEIGHT - 160,
        direction="down"
    )

    # Draw Enemy Mana
    draw_value_bar(
        screen,
        "mana",
        enemy.mana,
        MAX_MANA,
        SCREEN_WIDTH - 400,
        enemy.rect.y - 44,
        200,
        20
    )

    # Draw Enemy Health
    draw_value_bar(
        screen,
        "health",
        enemy.health,
        MAX_HEALTH,
        SCREEN_WIDTH - 400,
        enemy.rect.y - 22,
        200,
        20
    )

    enemy_buffs = [e for e in enemy.effects if e in BUFFS]
    enemy_debuffs = [e for e in enemy.effects if e in DEBUFFS]

    # Buffs ABOVE mana bar
    draw_effect_row(
        screen,
        enemy,
        enemy_buffs,
        SCREEN_WIDTH - 400,
        enemy.rect.y - 44,
        direction="up"
    )

    # Debuffs BELOW health bar
    draw_effect_row(
        screen,
        enemy,
        enemy_debuffs,
        SCREEN_WIDTH - 400,
        enemy.rect.y - 44,
        direction="down"
    )
    
    # Draw projectiles
    for projectile in projectiles:
        projectile.projectile_draw(screen)

    pygame.display.flip()

def recognize_spell():
    """
    Takes the rune drawn on canvas an inputs it into the CNN to be identified

    Args:
        canvas (pygame.Surface) - surface containing the rune to be identified

    Returns:
        spell_name (string) - name of the spell identified from rune
    """
    # TEMP: replace later with drawing recognition
    return random.choice(list(SPELL_LIST.keys()))

def deal_damage(caster, target, base_damage):
    """
    Calculates the damage of the spell and applies it to the target

    Args:
        caster (Entity) - entity who cast the spell
        target (Entity) - entity affected by the spell
        base_damage (int) - unmodified damage value of the spell cast

    Returns:
        damage (int) - modified damage value of the spell
    """
    damage = base_damage

    # -------------------
    # DEFENSIVE EFFECTS (target side)
    # -------------------
    if "shield" in target.effects:
        shield = target.effects["shield"]

        if shield.get("uses", 0) > 0:
            damage *= 0.5
            shield["uses"] -= 1

            if shield["uses"] <= 0:
                del target.effects["shield"]

    # (Future: armor, resistances, etc. go here)

    # -------------------
    # APPLY DAMAGE
    # -------------------
    target.health = clamp(target.health - damage, 0, target.max_health)

    # -------------------
    # OFFENSIVE EFFECTS (caster side)
    # -------------------

    # (Future: crits, on-hit effects, etc. go here)

    return damage

def cast_spell(spell_name, caster, target, projectiles):
    """
    Determines if a spell can be cast before casting it if able

    Args:
        spell_name (string) - name of spell to be cast
        caster (Entity) - entity who cast the spell
        target (Entity) - entity to be affected by the spell
        projectiles (array) - array of active Projectiles
    """
    spell = Spell.from_name(spell_name, SPELL_LIST)

    # CURSE CHECK
    if "curse" in caster.effects:
        blocked = caster.effects["curse"].get("blocked_spell")

        if blocked == spell_name:
            print(f"{spell_name} is blocked by curse!")
            return
    
    if not caster.spend_mana(spell.mana_cost):
        print("Not enough mana!")
        return
    
    # --- COUNTERSPELL LOGIC ---
    if spell_name == "counterspell":
        # Find a projectile targeting the caster
        for proj in projectiles:
            if proj.target == caster:
                projectiles.remove(proj)
                print("Projectile countered!")
                return  # stop here

        print("No projectile to counter!")
        return

    if spell.delivery == "projectile":
        projectiles.append(Projectile(caster, target, spell))
    else:
        resolve_spell_direct(spell, caster, target)

    if spell.delivery == "projectile":
        print(f"{caster} cast {spell_name}! (projectile launched)")
    else:
        print(f"{caster} cast {spell_name}! (instant)")

def resolve_spell_direct(spell, caster, target):
    """
    Applies the effects of an Instant spell

    Args:
        spell (Spell) - spell that was cast
        caster (Entity) - entity who cast the spell
        target (Entity) - entity to be affected by the spell
    """
    deal_damage(caster, target, spell.dmg)

    for effect, chance in spell.effects.items():
        total_chance = min(chance, 1.0)

        if random.random() < total_chance:
            if effect in EFFECTS:
                EFFECTS[effect](caster, target)
    
    print(f"{caster} casts {spell}!")
    print(f"{spell} damage:", spell.dmg)
    print(f"Player effects: ", caster.effects)
    print(f"Target effects: ", target.effects)
    

def resolve_spell(projectile):
    """
    Resolves the effects of a spell after its projectile collides with its target

    Args:
        projectile (array) - array of active Projectiles
    """
    caster = projectile.caster
    target = projectile.target
    spell = projectile.spell

    damage_dealt = deal_damage(caster, target, spell.dmg)

    if spell.leech:
        caster.health = clamp(
            caster.health + damage_dealt,
            0,
            caster.max_health
    )

    for effect, chance in spell.effects.items():
        total_chance = chance

        # Apply caster buffs to modify chance
        if effect == "burning" and "kindling" in caster.effects:
            total_chance += caster.effects["kindling"]["bonus_chance"]

        if effect == "freezing" and "glaciate" in caster.effects:
            total_chance += caster.effects["glaciate"]["bonus_chance"]

        total_chance = min(total_chance, 1.0)

        # Log the effect with the calculated chance
        print(f"{effect} base chance: {chance} → modified chance: {total_chance}")

        if random.random() < total_chance:
            if effect in EFFECTS:
                EFFECTS[effect](caster, target)

    print(f"Spell damage:", spell.dmg)
    print(f"Player effects: ", caster.effects)
    print(f"Target effects: ", target.effects)

def process_effects(entity, dt):
    """
    Applies the effects of a spell

    Args:
        entity (Entity) - entity who is effected
    """
    to_remove = []

    for effect, data in entity.effects.items():
        data["duration"] -= dt

        if effect == "burning":
            deal_damage(entity, entity, data["tick_damage"] * dt)

        # freezing doesn't deal damage, handled elsewhere

        if data["duration"] <= 0:
            to_remove.append(effect)

    for effect in to_remove:
        del entity.effects[effect]
    
    if "blind" in entity.effects:
        entity.effects["blind"]["duration"] -= dt

        if entity.effects["blind"]["duration"] <= 0:
            del entity.effects["blind"]

def regen_mana(player):
    """
    Determines then applies the mana regeneration rate of a player

    Args:
        player (Entity) - entity to have mana restored
    """
    current_time = pygame.time.get_ticks()

    if current_time - player.last_mana_regen >= 2000:
        regen_amount = 5

        if "freezing" in player.effects:
            slow = player.effects["freezing"]["slow"]
            regen_amount *= (1 - slow)

         # Check for Blitz effect and increase regen if it's active
        if "blitz" in player.effects:
            bonus_regen = player.effects["blitz"]["bonus_regen"]
            regen_amount += bonus_regen 

        player.mana = clamp(player.mana + regen_amount, 0, player.max_mana)
        player.last_mana_regen = current_time


# ---------------
# MAIN GAME LOOP
# ---------------
def run():
    """
    Runs the game
    """
    screen, canvas, player, sprites, state, enemy, spellbook, projectiles = init()
    clock = pygame.time.Clock()

    running = True
    while running:
        running = handle_events(state, canvas, player, enemy, projectiles)
        
        handle_drawing(canvas, state)

        dt = clock.tick(FPS) / 1000

        for projectile in projectiles[:]:
            finished = projectile.update(dt)

            if finished:
                resolve_spell(projectile)
                projectiles.remove(projectile)

        process_effects(player, dt)
        process_effects(enemy, dt)

        regen_mana(player)

        draw(screen, canvas, player, sprites, enemy, spellbook, projectiles)

    pygame.quit()

# ---------------
# ENTRY POINT
# ---------------
if __name__ == "__main__":
    run()
    #start_menu()