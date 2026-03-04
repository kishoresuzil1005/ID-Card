import json
import os
import sys
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from PIL import Image
from matplotlib.widgets import RectangleSelector

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
OUTPUT_JSON = os.path.join(BASE_DIR, "layout_config.json")

print("Select template:")
print("1 → FRONT")
print("2 → BACK")

choice = input("Enter 1 or 2: ")

if choice == "1":
    current_page = "front"
    TEMPLATE_PATH = os.path.join(TEMPLATE_DIR, "template_front.png")
    FIELDS = ["photo", "name", "designation", "emp_id"]
elif choice == "2":
    current_page = "back"
    TEMPLATE_PATH = os.path.join(TEMPLATE_DIR, "template_back.png")
    FIELDS = ["phone", "address", "dob", "blood", "emergency_contact"]
else:
    sys.exit()

if not os.path.exists(TEMPLATE_PATH):
    print("Template not found:", TEMPLATE_PATH)
    sys.exit()

if os.path.exists(OUTPUT_JSON):
    with open(OUTPUT_JSON, "r") as f:
        layout_data = json.load(f)
else:
    layout_data = {"front": {}, "back": {}}

fig, ax = plt.subplots()
img = Image.open(TEMPLATE_PATH)
ax.imshow(img)
plt.title(f"Mark fields for {current_page.upper()}")

current_index = 0
rectangles = []
current_rect = None

def on_select(eclick, erelease):
    global current_rect
    x1, y1 = int(eclick.xdata), int(eclick.ydata)
    x2, y2 = int(erelease.xdata), int(erelease.ydata)

    x = min(x1, x2)
    y = min(y1, y2)
    w = abs(x2 - x1)
    h = abs(y2 - y1)

    if current_rect:
        current_rect.remove()

    current_rect = Rectangle((x, y), w, h,
                             linewidth=2,
                             edgecolor="red",
                             facecolor="none")
    ax.add_patch(current_rect)
    fig.canvas.draw()

def confirm_box(event):
    global current_index, current_rect

    if event.key == "enter" and current_rect:
        bbox = current_rect.get_bbox()
        x = int(bbox.x0)
        y = int(bbox.y0)
        w = int(bbox.width)
        h = int(bbox.height)

        field = FIELDS[current_index]

        layout_data[current_page][field] = {
            "box": [x, y, w, h],
            "font_size": 30,
            "font": "Montserrat-Regular.ttf",
            "color": "#000000"
        }

        rectangles.append(current_rect)
        print(f"Saved → {field} = {[x,y,w,h]}")

        current_rect = None
        current_index += 1

        if current_index >= len(FIELDS):
            with open(OUTPUT_JSON, "w") as f:
                json.dump(layout_data, f, indent=4)
            print("Layout saved.")
            plt.close()

    elif event.key == "u":
        if rectangles:
            rect = rectangles.pop()
            rect.remove()
            current_index -= 1
            fig.canvas.draw()

selector = RectangleSelector(ax, on_select,
                             useblit=True,
                             button=[1],
                             interactive=True)

fig.canvas.mpl_connect("key_press_event", confirm_box)

plt.show()