import docx
import pypdf
import os
from PIL import Image

def analyze():
    print("=== ANALYZING DOCX ===")
    doc = docx.Document('app/src/main/res/layout/findora_documentation_black.docx')
    for i, p in enumerate(doc.paragraphs):
        for r in p.runs:
            if 'w:drawing' in r._r.xml:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(r._r.xml)
                blips = root.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/main}blip')
                for b in blips:
                    embed = b.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                    target = doc.part.rels[embed].target_ref if embed in doc.part.rels else 'unknown'
                    print(f"P[{i}]: text='{p.text[:60]}' -> {target}")

    print("\n=== ANALYZING 1.png to 12.png ===")
    for i in range(1, 13):
        path = f'app/src/main/res/layout/{i}.png'
        if os.path.exists(path):
            im = Image.open(path)
            print(f"{i}.png: size={im.size}")

if __name__ == '__main__':
    analyze()
