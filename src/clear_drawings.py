import os

folder_path = "drawings"

for filename in os.listdir(folder_path):
    file_path = os.path.join(folder_path, filename)

    if os.path.isfile(file_path):
        os.remove(file_path)

print("All drawing files deleted.")