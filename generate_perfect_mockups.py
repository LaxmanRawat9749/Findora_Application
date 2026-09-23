import os
from PIL import Image, ImageDraw, ImageFilter

def make_smartphone_mockup(screen_path, output_path):
    screen = Image.open(screen_path).convert("RGBA")
    sw, sh = screen.size

    # Standardize screen width to 720px
    target_sw = 720
    target_sh = int(sh * (target_sw / sw))
    screen_resized = screen.resize((target_sw, target_sh), Image.Resampling.LANCZOS)

    # Bezel dimensions
    bezel_lr = 16  # left/right bezel
    bezel_top = 18  # top bezel
    bezel_bot = 18  # bottom bezel

    phone_w = target_sw + 2 * bezel_lr
    phone_h = target_sh + bezel_top + bezel_bot

    corner_radius_outer = 50
    corner_radius_screen = 36

    # Canvas dimensions with padding for shadow
    pad_x = 40
    pad_y = 40
    canvas_w = phone_w + 2 * pad_x
    canvas_h = phone_h + 2 * pad_y

    canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))

    # 1. Soft Drop Shadow
    shadow_img = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_img)
    shadow_box = [pad_x - 2, pad_y + 14, pad_x + phone_w + 2, pad_y + phone_h + 18]
    shadow_draw.rounded_rectangle(shadow_box, radius=corner_radius_outer + 4, fill=(0, 0, 0, 70))
    shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(16))
    canvas.paste(shadow_img, (0, 0), shadow_img)

    # 2. Outer Phone Chassis (Sleek Dark Titanium / Silver Edge)
    chassis = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    c_draw = ImageDraw.Draw(chassis)
    phone_box = [pad_x, pad_y, pad_x + phone_w, pad_y + phone_h]
    
    # Outer metal band (silver-gray border)
    c_draw.rounded_rectangle(phone_box, radius=corner_radius_outer, fill=(24, 26, 30, 255), outline=(190, 195, 205, 255), width=2)
    
    # Inner bezel (deep obsidian black)
    inner_box = [pad_x + 3, pad_y + 3, pad_x + phone_w - 3, pad_y + phone_h - 3]
    c_draw.rounded_rectangle(inner_box, radius=corner_radius_outer - 3, fill=(10, 11, 14, 255))

    # 3. Screen Mask
    screen_mask = Image.new("L", (target_sw, target_sh), 0)
    s_mask_draw = ImageDraw.Draw(screen_mask)
    s_mask_draw.rounded_rectangle([0, 0, target_sw, target_sh], radius=corner_radius_screen, fill=255)

    screen_x = pad_x + bezel_lr
    screen_y = pad_y + bezel_top
    chassis.paste(screen_resized, (screen_x, screen_y), screen_mask)

    # 4. Subtle screen inner border
    c_draw.rounded_rectangle([screen_x, screen_y, screen_x + target_sw, screen_y + target_sh], radius=corner_radius_screen, outline=(30, 30, 35, 120), width=1)

    # 5. Top Speaker Ear-piece slit
    ear_w = 60
    ear_h = 4
    ear_x = pad_x + (phone_w - ear_w) // 2
    ear_y = pad_y + 8
    c_draw.rounded_rectangle([ear_x, ear_y, ear_x + ear_w, ear_y + ear_h], radius=2, fill=(45, 48, 55, 255))

    # 6. Punch-hole front camera
    cam_r = 10
    cam_x = pad_x + phone_w // 2
    cam_y = screen_y + 14
    c_draw.ellipse([cam_x - cam_r, cam_y - cam_r, cam_x + cam_r, cam_y + cam_r], fill=(4, 6, 10, 255), outline=(35, 38, 48, 220), width=1)
    c_draw.ellipse([cam_x - 3, cam_y - 3, cam_x + 1, cam_y + 1], fill=(20, 35, 65, 255))

    # 7. Hardware buttons
    # Left: Volume buttons
    c_draw.rounded_rectangle([pad_x - 3, pad_y + 110, pad_x, pad_y + 160], radius=2, fill=(160, 165, 175, 255))
    c_draw.rounded_rectangle([pad_x - 3, pad_y + 175, pad_x, pad_y + 225], radius=2, fill=(160, 165, 175, 255))
    # Right: Power button
    c_draw.rounded_rectangle([pad_x + phone_w, pad_y + 130, pad_x + phone_w + 3, pad_y + 195], radius=2, fill=(160, 165, 175, 255))

    # Composite chassis onto canvas
    canvas.paste(chassis, (0, 0), chassis)

    # Crop to content bounding box
    bbox = canvas.getbbox()
    if bbox:
        canvas = canvas.crop(bbox)

    canvas.save(output_path, "PNG")
    print(f"Generated mobile mockup: {output_path} ({canvas.size})")

def make_desktop_mockup(screen_path, output_path):
    screen = Image.open(screen_path).convert("RGBA")
    sw, sh = screen.size

    target_sw = 1400
    target_sh = int(sh * (target_sw / sw))
    screen_resized = screen.resize((target_sw, target_sh), Image.Resampling.LANCZOS)

    header_h = 38
    bezel = 10
    window_w = target_sw + 2 * bezel
    window_h = target_sh + header_h + 2 * bezel

    corner_r = 14
    pad = 40
    canvas_w = window_w + 2 * pad
    canvas_h = window_h + 2 * pad

    canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))

    # Shadow
    shadow_img = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow_img)
    s_box = [pad - 4, pad + 10, pad + window_w + 4, pad + window_h + 16]
    s_draw.rounded_rectangle(s_box, radius=corner_r + 4, fill=(0, 0, 0, 70))
    shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(18))
    canvas.paste(shadow_img, (0, 0), shadow_img)

    # Window chassis
    window = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    w_draw = ImageDraw.Draw(window)
    win_box = [pad, pad, pad + window_w, pad + window_h]

    # Outer frame
    w_draw.rounded_rectangle(win_box, radius=corner_r, fill=(242, 244, 248, 255), outline=(195, 200, 210, 255), width=2)

    # Window title/tab bar
    head_box = [pad, pad, pad + window_w, pad + bezel + header_h]
    w_draw.rounded_rectangle(head_box, radius=corner_r, fill=(230, 233, 240, 255))
    w_draw.rectangle([pad, pad + corner_r, pad + window_w, pad + bezel + header_h], fill=(230, 233, 240, 255))

    # Traffic light buttons (Close, Minimize, Maximize)
    btn_y = pad + bezel + 10
    btn_r = 6
    w_draw.ellipse([pad + 16, btn_y - btn_r, pad + 16 + 2 * btn_r, btn_y + btn_r], fill=(255, 95, 87, 255), outline=(225, 75, 67, 255), width=1)
    w_draw.ellipse([pad + 36, btn_y - btn_r, pad + 36 + 2 * btn_r, btn_y + btn_r], fill=(254, 188, 46, 255), outline=(224, 168, 36, 255), width=1)
    w_draw.ellipse([pad + 56, btn_y - btn_r, pad + 56 + 2 * btn_r, btn_y + btn_r], fill=(40, 201, 64, 255), outline=(30, 181, 54, 255), width=1)

    # Browser URL search bar
    url_box = [pad + 100, btn_y - 11, pad + window_w - 100, btn_y + 11]
    w_draw.rounded_rectangle(url_box, radius=6, fill=(255, 255, 255, 255), outline=(210, 215, 225, 255), width=1)

    # Screen paste
    screen_pos = (pad + bezel, pad + bezel + header_h)
    window.paste(screen_resized, screen_pos)
    w_draw.rectangle([screen_pos[0], screen_pos[1], screen_pos[0] + target_sw, screen_pos[1] + target_sh], outline=(205, 210, 220, 255), width=1)

    canvas.paste(window, (0, 0), window)

    bbox = canvas.getbbox()
    if bbox:
        canvas = canvas.crop(bbox)

    canvas.save(output_path, "PNG")
    print(f"Generated desktop mockup: {output_path} ({canvas.size})")

if __name__ == '__main__':
    os.makedirs('mockups', exist_ok=True)
    for i in range(1, 12):
        make_smartphone_mockup(f'app/src/main/res/layout/{i}.png', f'mockups/mockup_{i}.png')
    make_desktop_mockup('app/src/main/res/layout/12.png', 'mockups/mockup_12.png')
