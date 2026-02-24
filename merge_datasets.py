import os
import shutil

DATASET_DIR = "dataset"
INPUT_DIR = "input"   #change this if your input dataset is different, like maybe dataset(1)


def get_highest_index(directory):
    if not os.path.exists(directory):
        return 1

    nums = [
        int(f.split(".")[0])
        for f in os.listdir(directory)
        if f.endswith(".png") and f.split(".")[0].isdigit()
    ]

    return max(nums) if nums else 1

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def merge_spell_dir(spell_name):
    input_spell_dir = os.path.join(INPUT_DIR, spell_name)
    dataset_spell_dir = os.path.join(DATASET_DIR, spell_name)

    ensure_dir(dataset_spell_dir)

    highest = get_highest_index(dataset_spell_dir)
    files = sorted(os.listdir(input_spell_dir))
    added = 0

    for file in files:
        if not file.endswith(".png"):
            continue
        if file == "1.png":
            continue

        source_path = os.path.join(input_spell_dir, file)
        highest += 1
        new_name = f"{highest}.png"
        dest_path = os.path.join(dataset_spell_dir, new_name)
        shutil.copy2(source_path, dest_path)

        added += 1

    return added


def main():
    if not os.path.exists(INPUT_DIR):
        print("No input directory found.")
        return

    spell_dirs = [
        d for d in os.listdir(INPUT_DIR)
        if os.path.isdir(os.path.join(INPUT_DIR, d))
    ]

    total_added = 0
    for spell in spell_dirs:
        added = merge_spell_dir(spell)
        print(f"{spell}: added {added} files")
        total_added += added

    print(f"\nDone. Total files added to dataset: {total_added}")


main()