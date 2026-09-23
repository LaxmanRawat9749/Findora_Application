import pypdf
import os
from PIL import Image

def extract():
    reader = pypdf.PdfReader('app/src/main/res/layout/farahan_documentation.pdf')
    os.makedirs('farahan_screenshots', exist_ok=True)

    for p_num in range(54, 62):
        page = reader.pages[p_num-1]
        for idx, (name, img_obj) in enumerate(page.images.items()):
            clean_name = name.replace('/', '')
            out_path = f'farahan_screenshots/page_{p_num}_img_{idx}_{clean_name}.png'
            with open(out_path, 'wb') as f:
                f.write(img_obj.data)
            try:
                im = Image.open(out_path)
                print(f"{out_path}: size={im.size}")
            except Exception as e:
                print(f"{out_path}: {e}")

if __name__ == '__main__':
    extract()
