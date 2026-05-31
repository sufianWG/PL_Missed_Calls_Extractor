import shutil
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps
import pytesseract


TESSERACT_WINDOWS_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
]


def configure_tesseract() -> None:
    if shutil.which("tesseract"):
        return
    for path in TESSERACT_WINDOWS_PATHS:
        if Path(path).exists():
            pytesseract.pytesseract.tesseract_cmd = path
            return


def prepare_image(image_path: str) -> Image.Image:
    image = Image.open(image_path)
    image = ImageOps.exif_transpose(image).convert("L")

    width, height = image.size
    scale = 2 if width < 1800 else 1
    if scale > 1:
        image = image.resize((width * scale, height * scale), Image.Resampling.LANCZOS)

    image = ImageEnhance.Contrast(image).enhance(1.8)
    image = ImageEnhance.Sharpness(image).enhance(1.5)
    image = image.filter(ImageFilter.SHARPEN)
    return image


def image_to_text(image_path: str) -> str:
    configure_tesseract()
    image = prepare_image(image_path)
    config = "--oem 3 --psm 6"
    return pytesseract.image_to_string(image, lang="eng", config=config)
