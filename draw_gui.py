import tkinter as tk
from tkinter import simpledialog, messagebox
from PIL import Image, ImageDraw, ImageTk
import numpy as np
#import tensorflow as tf
import os
import time
from spells import SPELLS

CANVAS_SIZE = 280
MODEL_INPUT_SIZE = 28
DATASET_DIR = "dataset"


class RuneDrawer:
    def __init__(self, root):
        self.root = root
        self.root.title("Spellslinger – Rune System")

        self.canvas = tk.Canvas(root, width=CANVAS_SIZE, height=CANVAS_SIZE, bg="white")
        self.canvas.pack(side=tk.LEFT)

        self.side_panel = tk.Frame(root)
        self.side_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.label = tk.Label(self.side_panel, text="", font=("Comic Sans MS", 14))
        self.label.pack(pady=10)

        self.reference_label = tk.Label(self.side_panel)
        self.reference_label.pack(pady=10)

        self.undo_button = tk.Button(
            self.side_panel,
            text="Undo",
            command=self.undo_last
        )

        self.image = Image.new("L", (CANVAS_SIZE, CANVAS_SIZE), "white")
        self.draw = ImageDraw.Draw(self.image)

        #self.model = tf.keras.models.load_model("model/rune_classifier.h5")

        self.last_x = None
        self.last_y = None

        self.mode = None
        self.random_mode = False
        self.current_spell = None

        self.history = []

        self.choose_mode()

        self.canvas.bind("<ButtonPress-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.draw_rune)
        self.canvas.bind("<ButtonRelease-1>", self.end_draw)

    # MODE SELECTION

    def choose_mode(self):
        choice = messagebox.askquestion(
            "Mode Selection",
            "Choose a mode:\n\nYes = Identify Rune\nNo = Contribute to Dataset"
        )

        if choice == "yes":
            self.mode = "identify"
            self.label.config(text="Draw a rune to cast a spell")
        else:
            self.mode = "dataset"
            self.undo_button.pack(pady=5)
            self.choose_dataset_mode()

    def choose_dataset_mode(self):
        choice = messagebox.askquestion(
            "Dataset Mode",
            "Choose rune manually?\n\nYes = Choose Rune\nNo = Random Rune"
        )

        self.random_mode = (choice == "no")

        if self.random_mode:
            self.pick_random_spell()
        else:
            self.choose_spell()

    def choose_spell(self):
        lines = []
        spell_map = {}

        for spell in SPELLS.values():
            count = self.get_highest_index(spell)
            line = f"{spell} ({count})"
            lines.append(line)
            spell_map[line] = spell

        selection = simpledialog.askstring(
            "Choose Rune",
            "Available runes:\n" + ", ".join(lines)
        )

        if selection not in [s.split()[0] for s in spell_map]:
            messagebox.showerror("Error", "Invalid selection")
            self.choose_spell()
            return

        self.current_spell = selection
        self.load_reference_image()

    def pick_random_spell(self):
        self.current_spell = np.random.choice(list(SPELLS.values()))
        self.load_reference_image()

    # DRAW GUI

    def start_draw(self, event):
        self.last_x = event.x
        self.last_y = event.y

    def draw_rune(self, event):
        x, y = event.x, event.y
        self.canvas.create_line(
            self.last_x, self.last_y, x, y,
            width=10, capstyle=tk.ROUND
        )
        self.draw.line(
            (self.last_x, self.last_y, x, y),
            fill=0, width=10
        )
        self.last_x = x
        self.last_y = y

    def end_draw(self, event):
        if self.mode == "identify":
            self.identify_rune()
        else:
            self.save_rune()

        self.clear_canvas()

        if self.mode == "dataset" and self.random_mode:
            self.pick_random_spell()
        elif self.mode == "dataset":
            self.label.config(text=f"Draw this rune: {self.current_spell}")

    # DO NOT USE YET IT NO WORKY

    def identify_rune(self):
        rune = self.preprocess_image()
        prediction = self.model.predict(rune, verbose=0)
        spell_index = np.argmax(prediction)
        spell_name = SPELLS.get(spell_index, "Unknown Spell")
        self.label.config(text=f"Cast: {spell_name}")

    # DATASET MANAGEMENT

    def save_rune(self):
        spell_dir = self.get_spell_dir(self.current_spell)
        os.makedirs(spell_dir, exist_ok=True)

        next_index = self.get_highest_index(self.current_spell) + 1
        save_path = os.path.join(spell_dir, f"{next_index}.png")

        self.image.save(save_path)

        self.history.append(self.current_spell)

    def undo_last(self):
        if not self.history:
            return

        spell = self.history.pop()
        spell_dir = self.get_spell_dir(spell)

        highest = self.get_highest_index(spell)

        if highest <= 1:
            return

        path = os.path.join(spell_dir, f"{highest}.png")
        if os.path.exists(path):
            os.remove(path)

        self.current_spell = spell
        self.load_reference_image()
        self.label.config(text="Undoded. Redraw:")
        
    def load_reference_image(self):
        spell_dir = self.get_spell_dir(self.current_spell)
        ref_path = os.path.join(spell_dir, "1.png")

        if not os.path.exists(ref_path):
            self.reference_label.config(image="", text="No default img for this, fix it")
            return

        img = Image.open(ref_path).resize((140, 140))
        self.ref_image = ImageTk.PhotoImage(img)
        self.reference_label.config(image=self.ref_image)
        self.label.config(text=f"Draw this rune: {self.current_spell}")

    # UTILS

    def preprocess_image(self):
        img = self.image.resize((MODEL_INPUT_SIZE, MODEL_INPUT_SIZE))
        img = np.array(img) / 255.0
        img = img.reshape(1, MODEL_INPUT_SIZE, MODEL_INPUT_SIZE, 1)
        return img

    def clear_canvas(self):
        self.canvas.delete("all")
        self.image = Image.new("L", (CANVAS_SIZE, CANVAS_SIZE), "white")
        self.draw = ImageDraw.Draw(self.image)

    def get_spell_dir(self, spell):
        return os.path.join(
            DATASET_DIR,
            spell.lower().replace(" ", "_")
        )

    def get_highest_index(self, spell):
        spell_dir = self.get_spell_dir(spell)

        if not os.path.exists(spell_dir):
            return 1

        nums = [
            int(f.split(".")[0])
            for f in os.listdir(spell_dir)
            if f.endswith(".png") and f.split(".")[0].isdigit()
        ]

        return max(nums) if nums else 1