import os
import json
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FRONT_TEMPLATE = os.path.join(BASE_DIR, "templates", "template_front.png")
BACK_TEMPLATE = os.path.join(BASE_DIR, "templates", "template_back.png")
DEFAULT_PHOTO = os.path.join(BASE_DIR, "assets", "default_photo.png")
LAYOUT_FILE = os.path.join(BASE_DIR, "layout_config.json")


# ---------------------------
# Helpers
# ---------------------------

def load_layout():
    with open(LAYOUT_FILE, "r") as f:
        return json.load(f)


def hex_to_rgb(hexstr):
    hexstr = hexstr.lstrip("#")
    return tuple(int(hexstr[i:i+2], 16) for i in (0, 2, 4))


def get_font(font_name, size, bold=False):
    try:
        if bold:
            base, ext = os.path.splitext(font_name)
            font_name = base + "-Bold" + ext
        return ImageFont.truetype(
            os.path.join(BASE_DIR, "assets", "fonts", font_name), size
        )
    except:
        try:
            return ImageFont.truetype("arialbd.ttf" if bold else "arial.ttf", size)
        except:
            return ImageFont.load_default()


def normalize_box(cfg):
    return cfg["box"] if isinstance(cfg, dict) else cfg


# ---------------------------
# TEXT DRAWING
# ---------------------------

def draw_centered(draw, text, cfg, bold=False):
    box = normalize_box(cfg)
    x, y, w, h = map(int, box)

    font = get_font(
        cfg.get("font", "arial.ttf"),
        cfg.get("font_size", 28),
        bold
    )

    color = hex_to_rgb(cfg.get("color", "#000000"))

    # FIXED PROPER CENTER ALIGNMENT
    bbox = font.getbbox(text)

    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    text_x = x + (w - text_w) / 2 - bbox[0]
    text_y = y + (h - text_h) / 2 - bbox[1]

    draw.text((text_x, text_y), text, font=font, fill=color)


def draw_left_wrapped(draw, text, cfg):
    box = normalize_box(cfg)
    x, y, w, h = map(int, box)

    font = get_font(
        cfg.get("font", "arial.ttf"),
        cfg.get("font_size", 24),
        False
    )

    color = hex_to_rgb(cfg.get("color", "#FFFFFF"))

    words = text.split()
    lines = []
    current = ""

    for word in words:
        test = current + (" " if current else "") + word
        if draw.textlength(test, font=font) <= w:
            current = test
        else:
            lines.append(current)
            current = word

    if current:
        lines.append(current)

    line_height = font.size + 4
    total_height = line_height * len(lines)

    current_y = y + (h - total_height) / 2

    for line in lines:
        draw.text((x, current_y), line, font=font, fill=color)
        current_y += line_height


# ---------------------------
# PHOTO
# ---------------------------

def paste_photo(template, photo_path, cfg):
    box = normalize_box(cfg)
    x, y, w, h = map(int, box)

    if photo_path and os.path.exists(photo_path):
        photo = Image.open(photo_path).convert("RGB")
    else:
        photo = Image.open(DEFAULT_PHOTO).convert("RGB")

    min_side = min(photo.width, photo.height)
    left = (photo.width - min_side) // 2
    top = (photo.height - min_side) // 2
    photo = photo.crop((left, top, left + min_side, top + min_side))

    photo = photo.resize((w, h), Image.LANCZOS)

    mask = Image.new("L", (w, h), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle((0, 0, w, h), radius=30, fill=255)

    template.paste(photo, (x, y), mask)


# ---------------------------
# MAIN GENERATOR
# ---------------------------

def generate_id_card(
    name,
    emp_id,
    designation,
    phone,
    address,
    dob,
    blood,
    emergency_contact,
    photo_path,
    output_path
):

    layout = load_layout()

    # -------- FRONT --------
    front = Image.open(FRONT_TEMPLATE).convert("RGB")
    draw_front = ImageDraw.Draw(front)

    paste_photo(front, photo_path, layout["front"]["photo"])

    draw_centered(draw_front,
                  name.upper(),
                  layout["front"]["name"],
                  bold=True)

    draw_centered(draw_front,
                  designation.upper(),
                  layout["front"]["designation"],
                  bold=False)

    draw_centered(draw_front,
                  emp_id,
                  layout["front"]["emp_id"],
                  bold=False)

    # -------- BACK --------
    back = Image.open(BACK_TEMPLATE).convert("RGB")
    draw_back = ImageDraw.Draw(back)

    draw_left_wrapped(draw_back, phone,
                      layout["back"]["phone"])

    draw_left_wrapped(draw_back, address,
                      layout["back"]["address"])

    # DOB FIXED
    draw_left_wrapped(draw_back, dob,
                      layout["back"]["dob"])

    draw_left_wrapped(draw_back, blood,
                      layout["back"]["blood"])

    draw_left_wrapped(draw_back, emergency_contact,
                      layout["back"]["emergency_contact"])

    # -------- PDF --------
    width, height = front.size
    pdf = canvas.Canvas(output_path, pagesize=(width, height))

    pdf.drawImage(ImageReader(front), 0, 0, width=width, height=height)
    pdf.showPage()

    pdf.drawImage(ImageReader(back), 0, 0, width=width, height=height)
    pdf.showPage()

    pdf.save()

    print("ID Generated:", output_path)