import os
from PIL import Image, ImageDraw, ImageFilter, ImageOps

def create_mobile_mockup(screen_path, output_path):
    # Load screen
    screen = Image.open(screen_path).convert("RGBA")
    sw, sh = screen.size
    
    # Target device frame dimensions
    # Let's scale screen to a standardized aspect ratio (e.g., width=700, height=1400 or natural height)
    target_sw = 700
    target_sh = int(sh * (target_sw / sw))
    screen_resized = screen.resize((target_sw, target_sh), Image.Resampling.LANCZOS)
    
    # Bezel and frame thickness
    bezel = 18
    outer_w = target_sw + 2 * bezel
    outer_h = target_sh + 2 * bezel
    
    # Corner radius
    screen_radius = 42
    outer_radius = 54
    
    # Create mask for rounded screen
    screen_mask = Image.new("L", (target_sw, target_sh), 0)
    draw_smask = ImageDraw.Draw(screen_mask)
    draw_smask.rounded_rectangle([0, 0, target_sw, target_sh], radius=screen_radius, fill=255)
    
    # Create canvas for device
    canvas_padding = 40
    canvas_w = outer_w + 2 * canvas_padding
    canvas_h = outer_h + 2 * canvas_padding
    
    # Canvas with alpha
    device = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    
    # Draw soft drop shadow
    shadow = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    draw_shadow = ImageDraw.Draw(shadow)
    shadow_box = [
        canvas_padding - 4,
        canvas_padding + 12,
        canvas_padding + outer_w + 4,
        canvas_padding + outer_h + 16
    ]
    draw_shadow.rounded_rectangle(shadow_box, radius=outer_radius + 4, fill=(0, 0, 0, 80))
    shadow = shadow.filter(ImageFilter.GaussianBlur(16))
    device.paste(shadow, (0, 0), shadow)
    
    # Draw outer body / Titanium bezel
    draw_device = ImageDraw.Draw(device)
    body_box = [
        canvas_padding,
        canvas_padding,
        canvas_padding + outer_w,
        canvas_padding + outer_h
    ]
    # Outer metal edge (subtle gradient / silver titanium)
    draw_device.rounded_rectangle(body_box, radius=outer_radius, fill=(28, 30, 34, 255), outline=(180, 185, 195, 255), width=3)
    
    # Inner black bezel border
    inner_bezel_box = [
        canvas_padding + 4,
        canvas_padding + 4,
        canvas_padding + outer_w - 4,
        canvas_padding + outer_h - 4
    ]
    draw_device.rounded_rectangle(inner_bezel_box, radius=outer_radius - 4, fill=(12, 13, 15, 255))
    
    # Paste rounded screen
    screen_pos = (canvas_padding + bezel, canvas_padding + bezel)
    device.paste(screen_resized, screen_pos, screen_mask)
    
    # Draw subtle inner screen border
    draw_device.rounded_rectangle([screen_pos[0], screen_pos[1], screen_pos[0] + target_sw, screen_pos[1] + target_sh], radius=screen_radius, outline=(30, 30, 30, 100), width=1)
    
    # Draw punch-hole camera at top center of screen
    punch_w = 24
    punch_h = 24
    punch_x = screen_pos[0] + (target_sw - punch_w) // 2
    punch_y = screen_pos[1] + 16
    draw_device.ellipse([punch_x, punch_y, punch_x + punch_w, punch_y + punch_h], fill=(5, 5, 8, 255), outline=(40, 40, 50, 200), width=1)
    # Camera lens reflection dot
    draw_device.ellipse([punch_x + 6, punch_y + 6, punch_x + 10, punch_y + 10], fill=(20, 35, 60, 255))
    
    # Draw side buttons (Power on right, Volume on left)
    # Volume Up/Down on left
    draw_device.rounded_rectangle([canvas_padding - 4, canvas_padding + 120, canvas_padding, canvas_padding + 180], radius=2, fill=(140, 145, 155, 255))
    draw_device.rounded_rectangle([canvas_padding - 4, canvas_padding + 200, canvas_padding, canvas_padding + 260], radius=2, fill=(140, 145, 155, 255))
    # Power on right
    draw_device.rounded_rectangle([canvas_padding + outer_w, canvas_padding + 150, canvas_padding + outer_w + 4, canvas_padding + 230], radius=2, fill=(140, 145, 155, 255))
    
    # Crop transparent bounding box
    bbox = device.getbbox()
    if bbox:
        device = device.crop(bbox)
        
    device.save(output_path, "PNG")
    print(f"Generated mobile mockup: {output_path} ({device.size})")

def create_desktop_mockup(screen_path, output_path):
    screen = Image.open(screen_path).convert("RGBA")
    sw, sh = screen.size
    
    target_sw = 1400
    target_sh = int(sh * (target_sw / sw))
    screen_resized = screen.resize((target_sw, target_sh), Image.Resampling.LANCZOS)
    
    header_h = 36
    bezel = 12
    outer_w = target_sw + 2 * bezel
    outer_h = target_sh + header_h + 2 * bezel
    
    radius = 16
    canvas_padding = 40
    canvas_w = outer_w + 2 * canvas_padding
    canvas_h = outer_h + 2 * canvas_padding
    
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    
    # Shadow
    shadow = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    draw_shadow = ImageDraw.Draw(shadow)
    shadow_box = [canvas_padding - 6, canvas_padding + 10, canvas_padding + outer_w + 6, canvas_padding + outer_h + 18]
    draw_shadow.rounded_rectangle(shadow_box, radius=radius + 4, fill=(0, 0, 0, 75))
    shadow = shadow.filter(ImageFilter.GaussianBlur(20))
    canvas.paste(shadow, (0, 0), shadow)
    
    draw = ImageDraw.Draw(canvas)
    window_box = [canvas_padding, canvas_padding, canvas_padding + outer_w, canvas_padding + outer_h]
    
    # Outer frame (modern dark silver / titanium)
    draw.rounded_rectangle(window_box, radius=radius, fill=(245, 246, 248, 255), outline=(200, 205, 215, 255), width=2)
    
    # Header bar
    header_box = [canvas_padding, canvas_padding, canvas_padding + outer_w, canvas_padding + bezel + header_h]
    draw.rounded_rectangle(header_box, radius=radius, fill=(232, 235, 240, 255))
    # Fill bottom corners of header
    draw.rectangle([canvas_padding, canvas_padding + radius, canvas_padding + outer_w, canvas_padding + bezel + header_h], fill=(232, 235, 240, 255))
    
    # Mac style window control buttons (Red, Yellow, Green)
    btn_y = canvas_padding + bezel + 10
    btn_r = 6
    draw.ellipse([canvas_padding + 16, btn_y - btn_r, canvas_padding + 16 + 2 * btn_r, btn_y + btn_r], fill=(255, 95, 87, 255))
    draw.ellipse([canvas_padding + 36, btn_y - btn_r, canvas_padding + 36 + 2 * btn_r, btn_y + btn_r], fill=(254, 188, 46, 255))
    draw.ellipse([canvas_padding + 56, btn_y - btn_r, canvas_padding + 56 + 2 * btn_r, btn_y + btn_r], fill=(40, 201, 64, 255))
    
    # Browser URL bar
    url_box = [canvas_padding + 100, btn_y - 10, canvas_padding + outer_w - 100, btn_y + 10]
    draw.rounded_rectangle(url_box, radius=6, fill=(255, 255, 255, 255), outline=(215, 220, 228, 255), width=1)
    
    # Screen area
    screen_pos = (canvas_padding + bezel, canvas_padding + bezel + header_h)
    canvas.paste(screen_resized, screen_pos)
    
    # Inner screen border
    draw.rectangle([screen_pos[0], screen_pos[1], screen_pos[0] + target_sw, screen_pos[1] + target_sh], outline=(210, 215, 225, 255), width=1)
    
    bbox = canvas.getbbox()
    if bbox:
        canvas = canvas.crop(bbox)
        
    canvas.save(output_path, "PNG")
    print(f"Generated desktop mockup: {output_path} ({canvas.size})")

if __name__ == '__main__':
    os.makedirs('mockups', exist_ok=True)
    for i in range(1, 12):
        create_mobile_mockup(f'app/src/main/res/layout/{i}.png', f'mockups/mockup_{i}.png')
    create_desktop_mockup('app/src/main/res/layout/12.png', 'mockups/mockup_12.png')
