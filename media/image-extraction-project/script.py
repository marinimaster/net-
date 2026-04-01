import os
from pathlib import Path
from PIL import Image, ImageOps
import pytesseract

# ===== CONFIG =====
INPUT_DIR = "goodnotes-imgs"
OUTPUT_DIR = "output"
MERGED_FILE = "merged_output.txt"
LANGUAGE = "eng"  # change if needed

# Optional: force path if needed
TESSERACT_PATH = "/usr/bin/tesseract"

VALID_EXTENSIONS = (".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp")

# ===== SETUP =====
input_path = Path(INPUT_DIR)
output_path = Path(OUTPUT_DIR)

if not input_path.exists():
    raise FileNotFoundError(f"Input directory not found: {INPUT_DIR}")

output_path.mkdir(parents=True, exist_ok=True)

# Set tesseract path if needed
if os.path.exists(TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

merged_lines = []

# ===== PREPROCESSING FUNCTION =====
def preprocess(image: Image.Image) -> Image.Image:
    # Convert to grayscale
    image = ImageOps.grayscale(image)

    # Increase contrast (simple normalization)
    image = ImageOps.autocontrast(image)

    # Optional: resize if too small (improves OCR)
    if image.width < 1000:
        image = image.resize((image.width * 2, image.height * 2))

    return image

# ===== PROCESSING =====
for img_file in sorted(input_path.iterdir()):
    if img_file.suffix.lower() not in VALID_EXTENSIONS:
        continue

    try:
        print(f"[INFO] Processing: {img_file.name}")

        image = Image.open(img_file)
        image = preprocess(image)

        text = pytesseract.image_to_string(image, lang=LANGUAGE)

        # Clean text (basic)
        text = text.strip()

        # Save individual file
        out_file = output_path / f"{img_file.stem}.txt"
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(text)

        # Append to merged output
        merged_lines.append(f"===== {img_file.name} =====\n{text}\n")

    except Exception as e:
        print(f"[ERROR] Failed: {img_file.name} -> {e}")

# ===== MERGED OUTPUT =====
merged_path = output_path / MERGED_FILE

with open(merged_path, "w", encoding="utf-8") as f:
    f.write("\n".join(merged_lines))

print(f"[DONE] Processed files saved in: {OUTPUT_DIR}")
print(f"[DONE] Merged output: {merged_path}")
