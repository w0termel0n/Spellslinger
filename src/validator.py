import os
import numpy as np
from PIL import Image
from skimage.morphology import skeletonize
from collections import defaultdict

DATASET_DIR = "dataset"


class RunePathValidator:

    DEFAULT_THRESHOLD = 0.895

    # Per-spell overrides — any spell not listed here uses DEFAULT_THRESHOLD
    THRESHOLDS = {
        "blitz": 0.90,
        "blindness": 0.885,
        "curse": 0.75,
        "fireball": 0.90, # new line
        "roulette": 0.875,
        "shield": 0.85,
        "spike": 0.85
    }

    def __init__(self, samples=64):
        self.samples = samples
        # spell_name (str) → list of (x, y) tuples, pre-computed at startup
        self._templates = {}
        self._precompute_all_templates()

    def _spell_name_to_dir(self, spell_name):
        return os.path.join(DATASET_DIR, spell_name.lower().replace(" ", "_"))

    def _precompute_all_templates(self):
        """
        Walk every subdirectory of DATASET_DIR, load 1.png as the reference
        image, skeletonize it, and store the resulting path keyed by spell name
        (derived from the folder name, reversing the lower/underscore transform).
        """
        if not os.path.isdir(DATASET_DIR):
            print(f"[Validator] Dataset directory '{DATASET_DIR}' not found — no templates loaded.")
            return

        for folder in os.listdir(DATASET_DIR):
            ref_path = os.path.join(DATASET_DIR, folder, "1.png")
            if not os.path.isfile(ref_path):
                continue

            # Spell names are just the folder name as-is (e.g. "fireball", "frostbite")
            spell_name = folder

            path = self.image_to_stroke_path(ref_path)
            if path is not None:
                self._templates[spell_name] = path
                print(f"[Validator] Loaded template: {spell_name} ({len(path)} pts)")
            else:
                print(f"[Validator] WARNING: Could not extract path from {ref_path}")

    # ----------------------------
    # Skeletonization + path extraction
    # ----------------------------

    def image_to_stroke_path(self, image_path):
        """
        Load a reference PNG, skeletonize it, then extract an ordered
        point path by walking the skeleton graph from one endpoint to another.
        Returns a list of (x, y) tuples, or None on failure.
        """
        img = Image.open(image_path).convert("L")
        arr = np.array(img)

        # Binarize: treat dark pixels as the stroke (True = stroke pixel)
        binary = arr < 128

        if binary.sum() < 10:
            return None

        # Skeletonize to 1-pixel-wide path
        skeleton = skeletonize(binary)

        # Build adjacency graph from skeleton pixels
        coords = list(zip(*np.where(skeleton)))  # list of (row, col)
        if len(coords) < 2:
            return None

        coord_set = set(coords)
        neighbors = defaultdict(list)

        for (r, c) in coords:
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nb = (r + dr, c + dc)
                    if nb in coord_set:
                        neighbors[(r, c)].append(nb)

        # Find endpoints (degree 1) or just pick any node if none exist (closed loop)
        endpoints = [n for n, nbrs in neighbors.items() if len(nbrs) == 1]
        start = endpoints[0] if endpoints else coords[0]

        # Walk the skeleton greedily from the start endpoint
        path = []
        visited = set()
        current = start

        while True:
            path.append(current)
            visited.add(current)
            unvisited = [n for n in neighbors[current] if n not in visited]
            if not unvisited:
                break
            # prefer neighbors closest to current direction for smoother path
            if len(path) >= 2:
                prev = path[-2]
                dr = current[0] - prev[0]
                dc = current[1] - prev[1]
                unvisited.sort(
                    key=lambda n: -((n[0] - current[0]) * dr + (n[1] - current[1]) * dc)
                )
            current = unvisited[0]

        if len(path) < 2:
            return None

        # Convert (row, col) → (x, y)
        return [(c, r) for (r, c) in path]

    # ----------------------------
    # Basic geometry utilities
    # ----------------------------

    def distance(self, a, b):
        return np.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)

    def path_length(self, pts):
        return sum(
            self.distance(pts[i - 1], pts[i])
            for i in range(1, len(pts))
        )

    # ----------------------------
    # Safety check
    # ----------------------------

    def is_valid_stroke(self, pts):
        if pts is None or len(pts) < 15:
            return False
        total = self.path_length(pts)
        if total < 20:
            return False
        return True

    # ----------------------------
    # Resampling
    # ----------------------------

    def resample(self, points):
        if len(points) < 2:
            return points

        total = self.path_length(points)
        if total < 1e-6:
            return points[:self.samples]

        step = total / (self.samples - 1)
        new_points = [points[0]]
        D = 0.0
        i = 1
        safety = 0

        while i < len(points):
            safety += 1
            if safety > 50000:
                break

            p1 = points[i - 1]
            p2 = points[i]
            d = self.distance(p1, p2)

            if d == 0:
                i += 1
                continue

            if (D + d) >= step:
                t = (step - D) / d
                nx = p1[0] + t * (p2[0] - p1[0])
                ny = p1[1] + t * (p2[1] - p1[1])
                new_points.append((nx, ny))
                D = 0.0
                i += 1
            else:
                D += d
                i += 1

        while len(new_points) < self.samples:
            new_points.append(points[-1])

        return new_points[:self.samples]

    # ----------------------------
    # Normalization
    # ----------------------------

    def normalize(self, pts):
        pts = np.array(pts, dtype=np.float32)
        pts -= pts.mean(axis=0)
        norm = np.linalg.norm(pts)
        if norm > 1e-6:
            pts /= norm
        return pts

    # ----------------------------
    # Feature extraction
    # ----------------------------

    def turning_angles(self, pts):
        """
        Compute the signed turning angle at each interior point of the path.
        This captures the directional shape of the stroke regardless of scale.
        A scribble will have a very different angle signature than a clean rune.
        """
        pts = np.array(pts, dtype=np.float32)
        angles = []
        for i in range(1, len(pts) - 1):
            v1 = pts[i] - pts[i - 1]
            v2 = pts[i + 1] - pts[i]
            n1 = np.linalg.norm(v1)
            n2 = np.linalg.norm(v2)
            if n1 < 1e-6 or n2 < 1e-6:
                angles.append(0.0)
                continue
            v1 /= n1
            v2 /= n2
            # signed angle via cross and dot
            cross = v1[0] * v2[1] - v1[1] * v2[0]
            dot = np.clip(np.dot(v1, v2), -1.0, 1.0)
            angles.append(np.arctan2(cross, dot))
        return np.array(angles, dtype=np.float32)

    def path_length_ratio(self, input_pts, template_pts):
        """
        Ratio of input path length to template path length, both normalized
        to their bounding box diagonal so canvas size differences don't matter.
        A scribble will have a much higher ratio than a clean rune.
        Returns a penalty in [0, 1] — 1.0 means lengths match perfectly.
        """
        def normalized_length(pts):
            pts = np.array(pts, dtype=np.float32)
            bbox = pts.max(axis=0) - pts.min(axis=0)
            diag = np.linalg.norm(bbox)
            if diag < 1e-6:
                return 0.0
            total = sum(
                np.linalg.norm(np.array(pts[i]) - np.array(pts[i - 1]))
                for i in range(1, len(pts))
            )
            return total / diag

        r_input = normalized_length(input_pts)
        r_template = normalized_length(template_pts)

        if r_template < 1e-6:
            return 0.0

        ratio = r_input / r_template
        # penalize if input path is more than 2x longer than template
        # (scribbles will be way over this)
        if ratio > 2.0:
            return 1.0 / ratio
        return 1.0 - abs(ratio - 1.0) * 0.3

    # ----------------------------
    # Scoring
    # ----------------------------

    def shape_score(self, a, b):
        """Point-cloud geometric similarity (existing approach)."""
        a_norm = self.normalize(self.resample(list(a)))
        b_norm = self.normalize(self.resample(list(b)))
        score_fwd = 1.0 / (1.0 + np.mean(np.linalg.norm(a_norm - b_norm, axis=1)))
        score_rev = 1.0 / (1.0 + np.mean(np.linalg.norm(a_norm - b_norm[::-1], axis=1)))
        return max(score_fwd, score_rev)

    def angle_score(self, a, b):
        """Turning angle profile similarity."""
        a_resampled = self.resample(list(a))
        b_resampled = self.resample(list(b))
        a_angles = self.turning_angles(a_resampled)
        b_angles = self.turning_angles(b_resampled)
        # both are length samples-2, so they're already aligned
        diff = np.mean(np.abs(a_angles - b_angles))
        # diff is in radians; pi is maximally wrong
        return 1.0 - (diff / np.pi)

    def path_score(self, a, b):
        """
        Combined score from three independent signals:
          - shape_score:  point-cloud geometry match
          - angle_score:  turning angle profile match (catches scribbles)
          - length_ratio: path length relative to bounding box (catches overdrawing)
        All three must be reasonable for a high overall score.
        """
        s_shape  = self.shape_score(a, b)
        s_angle  = self.angle_score(a, b)
        s_length = self.path_length_ratio(a, b)

        print(f"  [shape={s_shape:.3f}  angle={s_angle:.3f}  length={s_length:.3f}]")

        # Weighted combination — angle and length are the scribble-catchers
        return 0.4 * s_shape + 0.4 * s_angle + 0.2 * s_length

    # ----------------------------
    # MAIN API
    # ----------------------------

    def validate(self, input_points, spell_name):
        """
        input_points : list of (x, y) tuples from the user's mouse stroke
        spell_name   : string matching a key in SPELLS (e.g. "fireball")
        """
        threshold = self.THRESHOLDS.get(spell_name, self.DEFAULT_THRESHOLD)
        if not self.is_valid_stroke(input_points):
            return False, 0.0

        template_points = self._templates.get(spell_name)

        if not self.is_valid_stroke(template_points):
            print(f"[Validator] No usable template for spell: '{spell_name}'")
            return False, 0.0

        score = self.path_score(input_points, template_points)
        return score >= threshold, score