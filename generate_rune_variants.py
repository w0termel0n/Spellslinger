import os
import cv2
import numpy as np
import random

DATASET_DIR = "dataset"
VARIATIONS_PER_RUNE = 50

# ============================
# FILE NUMBERING
# ============================

def get_highest_index(directory):

    if not os.path.exists(directory):
        return 0

    highest = 0

    for file in os.listdir(directory):

        if not file.endswith(".png"):
            continue

        name = file.split(".")[0]

        if name.isdigit():
            num = int(name)
            if num > highest:
                highest = num

    return highest


# ============================
# STRUCTURAL VARIATION ENGINE
# ============================

def random_affine(img):
    h, w = img.shape

    # Random triangle in original image
    pts1 = np.float32([
        [0, 0],
        [w, 0],
        [0, h]
    ])

    max_shift = 0.25

    pts2 = np.float32([
        [random.uniform(0, w*max_shift), random.uniform(0, h*max_shift)],
        [w - random.uniform(0, w*max_shift), random.uniform(0, h*max_shift)],
        [random.uniform(0, w*max_shift), h - random.uniform(0, h*max_shift)]
    ])

    M = cv2.getAffineTransform(pts1, pts2)

    warped = cv2.warpAffine(
        img,
        M,
        (w, h),
        borderValue=255
    )

    return warped


def random_perspective(img):
    h, w = img.shape

    max_shift = 0.3

    pts1 = np.float32([
        [0, 0],
        [w, 0],
        [w, h],
        [0, h]
    ])

    pts2 = np.float32([
        [random.uniform(0, w*max_shift), random.uniform(0, h*max_shift)],
        [w - random.uniform(0, w*max_shift), random.uniform(0, h*max_shift)],
        [w - random.uniform(0, w*max_shift), h - random.uniform(0, h*max_shift)],
        [random.uniform(0, w*max_shift), h - random.uniform(0, h*max_shift)]
    ])

    M = cv2.getPerspectiveTransform(pts1, pts2)

    warped = cv2.warpPerspective(
        img,
        M,
        (w, h),
        borderValue=255
    )

    return warped


def random_scale_translate(img):
    h, w = img.shape

    scale = random.uniform(0.90, 1.10)

    cx, cy = w/2, h/2

    M = np.float32([
        [scale, 0, cx - scale*cx],
        [0, scale, cy - scale*cy]
    ])

    warped = cv2.warpAffine(
        img,
        M,
        (w, h),
        borderValue=255
    )

    return warped


def random_rotate(img):
    h, w = img.shape

    angle = random.uniform(-15, 15)

    M = cv2.getRotationMatrix2D(
        (w//2, h//2),
        angle,
        random.uniform(0.8, 1.2)
    )

    warped = cv2.warpAffine(
        img,
        M,
        (w, h),
        borderValue=255
    )

    return warped


def elastic_warp(img, alpha, sigma):
    """
    alpha = strength of distortion
    sigma = smoothness of distortion

    higher alpha = more wobble
    higher sigma = smoother curves
    """

    h, w = img.shape

    # generate smooth random displacement fields
    dx = np.random.randn(h, w).astype(np.float32)
    dy = np.random.randn(h, w).astype(np.float32)

    dx = cv2.GaussianBlur(dx, (0,0), sigma) * alpha
    dy = cv2.GaussianBlur(dy, (0,0), sigma) * alpha

    # create coordinate grid
    x, y = np.meshgrid(np.arange(w), np.arange(h))

    map_x = (x + dx).astype(np.float32)
    map_y = (y + dy).astype(np.float32)

    warped = cv2.remap(
        img,
        map_x,
        map_y,
        interpolation=cv2.INTER_NEAREST,  # preserves sharp stroke edges
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=255
    )

    return warped


# Combine transforms randomly
def generate_variation(base_img):

    img = base_img.copy()

    transforms = [
        random_affine,
        random_perspective,
        random_rotate,
        random_scale_translate
    ]

    random.shuffle(transforms)

    for t in transforms[:random.randint(1, 3)]:
        img = t(img)

    img = elastic_warp(img, alpha=30, sigma=8)

    return img


# ============================
# MAIN GENERATION LOOP
# ============================

def generate_for_spell(spell_dir):

    base_path = os.path.join(spell_dir, "1.png")

    if not os.path.exists(base_path):
        print(f"Skipping {spell_dir}, no 1.png")
        return 0

    base_img = cv2.imread(base_path, cv2.IMREAD_GRAYSCALE)

    highest = get_highest_index(spell_dir)

    count = 0

    for i in range(VARIATIONS_PER_RUNE):

        highest += 1

        variation = generate_variation(base_img)

        save_path = os.path.join(
            spell_dir,
            f"{highest}.png"
        )

        cv2.imwrite(save_path, variation)

        count += 1

    return count


def main():

    total = 0

    for spell in os.listdir(DATASET_DIR):

        spell_dir = os.path.join(DATASET_DIR, spell)

        if not os.path.isdir(spell_dir):
            continue

        added = generate_for_spell(spell_dir)

        print(f"{spell}: added {added}")
        total += added
        #break

    print(f"\nTotal added: {total}")


if __name__ == "__main__":
    main()