from PIL import Image, ImageDraw

img = Image.new("RGB", (150, 200), "gray")
draw = ImageDraw.Draw(img)
draw.text((20, 80), "NO PHOTO", fill="white")
img.save("default_photo.png")