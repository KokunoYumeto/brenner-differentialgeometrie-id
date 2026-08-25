from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1] / "tmp" / "pdfs" / "unit06-render"
PAGES = [ROOT / f"page-{number:03d}.png" for number in range(1, 106)]


def main() -> None:
    missing = [str(path) for path in PAGES if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing rendered pages: {missing}")

    thumb_width, thumb_height = 390, 505
    label_height = 28
    font = ImageFont.load_default()

    for sheet_number in range(7):
        canvas = Image.new(
            "RGB",
            (4 * thumb_width, 4 * (thumb_height + label_height)),
            "white",
        )
        draw = ImageDraw.Draw(canvas)
        first = sheet_number * 16
        for index, path in enumerate(PAGES[first : first + 16]):
            with Image.open(path) as source:
                image = source.convert("RGB")
            image.thumbnail(
                (thumb_width - 12, thumb_height - 12),
                Image.Resampling.LANCZOS,
            )
            column, row = index % 4, index // 4
            x = column * thumb_width + (thumb_width - image.width) // 2
            y = (
                row * (thumb_height + label_height)
                + label_height
                + (thumb_height - image.height) // 2
            )
            canvas.paste(image, (x, y))
            draw.text(
                (column * thumb_width + 8, row * (thumb_height + label_height) + 6),
                path.stem,
                fill="black",
                font=font,
            )
        canvas.save(ROOT / f"contact-{sheet_number + 1:02d}.png", optimize=True)

    print(f"Regenerated 7 contact sheets from {len(PAGES)} final page PNGs.")


if __name__ == "__main__":
    main()
