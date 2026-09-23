import os
import glob
from PIL import Image

def inspect_images():
    print("=== INSPECTING 1.png to 12.png ===")
    for i in range(1, 13):
        path = f'app/src/main/res/layout/{i}.png'
        if os.path.exists(path):
            img = Image.open(path)
            print(f"{i}.png: size={img.size}, mode={img.mode}")
        else:
            print(f"{i}.png: NOT FOUND")

if __name__ == '__main__':
    inspect_images()
