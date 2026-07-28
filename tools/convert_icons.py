from pathlib import Path
import subprocess
from PIL import Image

BASE = Path.home() / "PiDash"

SRC = BASE / "hud" / "icons_svg"
DST = BASE / "hud" / "icons"

DST.mkdir(exist_ok=True)

SIZE = 64

for svg in SRC.glob("*.svg"):

    png = DST / (svg.stem + ".png")

    print(f"Convirtiendo {svg.name}")

    subprocess.run([
        "rsvg-convert",
        "-w", str(SIZE),
        "-h", str(SIZE),
        "-o", str(png),
        str(svg)
    ])

    img = Image.open(png).convert("RGBA")

    data = []

    for r, g, b, a in img.getdata():

        if a == 0:
            data.append((0, 0, 0, 0))
        else:
            data.append((255, 255, 255, a))

    img.putdata(data)
    img.save(png)

print()
print("================================")
print(" Iconos convertidos correctamente")
print("================================")