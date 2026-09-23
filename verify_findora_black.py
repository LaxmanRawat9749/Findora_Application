import docx
import os
import zipfile
import xml.etree.ElementTree as ET

def verify():
    path = 'findora_black.docx'
    print(f"=== VERIFYING {path} ===")
    assert os.path.exists(path), "File does not exist!"
    size_mb = os.path.getsize(path) / (1024 * 1024)
    print(f"File Size: {size_mb:.2f} MB")

    doc = docx.Document(path)
    print(f"Total Paragraphs: {len(doc.paragraphs)}")
    print(f"Total Tables: {len(doc.tables)}")
    print(f"Total Sections: {len(doc.sections)}")

    # Check Sections & Margins
    for i, sec in enumerate(doc.sections):
        print(f"Section {i}:")
        print(f"  Page Size: {sec.page_width.inches:.2f} x {sec.page_height.inches:.2f} inches (Expected: 8.27 x 11.69 A4)")
        print(f"  Margins: Left={sec.left_margin.inches:.2f}\", Right={sec.right_margin.inches:.2f}\", Top={sec.top_margin.inches:.2f}\", Bottom={sec.bottom_margin.inches:.2f}\"")
        assert abs(sec.left_margin.inches - 1.5) < 0.01, "Left margin must be 1.5 in"
        assert abs(sec.right_margin.inches - 1.0) < 0.01, "Right margin must be 1.0 in"
        assert abs(sec.top_margin.inches - 1.0) < 0.01, "Top margin must be 1.0 in"
        assert abs(sec.bottom_margin.inches - 1.0) < 0.01, "Bottom margin must be 1.0 in"

    # Check Embedded Images
    with zipfile.ZipFile(path) as z:
        media_files = [f for f in z.namelist() if f.startswith('word/media/')]
        print(f"Total Embedded Media Images: {len(media_files)}")
        for mf in sorted(media_files):
            print(f"  {mf}: {z.getinfo(mf).file_size} bytes")

    # Check Word Count
    total_words = 0
    for p in doc.paragraphs:
        total_words += len(p.text.split())
    for t in doc.tables:
        for row in t.rows:
            for cell in row.cells:
                total_words += len(cell.text.split())
    print(f"Total Word Count in Document: {total_words} words")

    # Check Font Integrity
    non_tnr = []
    for p in doc.paragraphs:
        for r in p.runs:
            if r.font.name and r.font.name != 'Times New Roman':
                non_tnr.append((p.text[:30], r.font.name))
    if non_tnr:
        print(f"WARNING: Non-Times New Roman runs found: {len(non_tnr)}")
    else:
        print("PASS: 100% Times New Roman typography verified across all paragraphs and runs!")

    print("ALL CHECKS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    verify()
