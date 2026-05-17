## PDF to PNG

```python
import os
from pdf2image import convert_from_path

pdf_path = '/content/ae-philo-2025-e28093-composition-2-de-philosophie-sur-programme-e28093-12520.pdf'
output_folder = '/content/ae-philo-2025-images'

os.makedirs(output_folder, exist_ok=True)
images = convert_from_path(pdf_path, dpi=300)

for i, image in enumerate(images):
    image_name = f'page_{i+1:03d}.png'
    image.save(os.path.join(output_folder, image_name), 'PNG')
    print(f"Saved: {image_name}")
```

## Remove le numéro de page

```python
import os
from PIL import Image

image_folder = '/content/ae-philo-2025-images'
images_files = [f for f in os.listdir(image_folder) if f.endswith('.png')]

def remove_number_box(image_path):
    with Image.open(image_path) as img:
        width, height = img.size
        
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        
        # Common dimensions for the number box in this pipeline:
        rect_coords = [width * 0.88, height * 0.93, width, height]
        draw.rectangle(rect_coords, fill="white")
        
        img.save(image_path)

print(f"Processing {len(images_files)} images to remove numbering box...")
for filename in sorted(images_files):
    remove_number_box(os.path.join(image_folder, filename))
    print(f"Cleaned: {filename}")

print("\nNumbering removal complete.")
```


```python
import os
from PIL import Image

target_y = 647
images_to_crop = [
    '/content/ae-philo-2025-images/page_002.png',
    '/content/ae-philo-2025-images/page_006.png',
    '/content/ae-philo-2025-images/page_010.png'
]

for img_path in images_to_crop:
    if os.path.exists(img_path):
        with Image.open(img_path) as img:
            width, height = img.size
            # Crop defining the box: (left, top, right, bottom)
            # We keep from target_y to the bottom of the image
            cropped_img = img.crop((0, target_y, width, height))
            cropped_img.save(img_path)
            print(f"Cropped {os.path.basename(img_path)}: New size {width}x{height - target_y}")
    else:
        print(f"Warning: {img_path} not found.")
```


```python
import os
from PIL import Image

target_y = 1351
images_to_crop = [
    '/content/ae-philo-2025-images/page_001.png',
    '/content/ae-philo-2025-images/page_005.png',
    '/content/ae-philo-2025-images/page_009.png'
]

for img_path in images_to_crop:
    if os.path.exists(img_path):
        with Image.open(img_path) as img:
            width, height = img.size
            cropped_img = img.crop((0, target_y, width, height))
            cropped_img.save(img_path)
            print(f"Cropped {os.path.basename(img_path)}: New size {width}x{height - target_y}")
    else:
        print(f"Warning: {img_path} not found.")
```

## Après avoir installé la bonne version de `transformers`


```python
from transformers import AutoProcessor, AutoModelForImageTextToText
import torch

processor = AutoProcessor.from_pretrained("zai-org/GLM-OCR")

model = AutoModelForImageTextToText.from_pretrained(
    "zai-org/GLM-OCR",
    torch_dtype=torch.float16,
    device_map="auto",
)
```




```python
import os
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

import gc
import glob
import torch
import pandas as pd
from PIL import Image
device = "cuda"
model.eval()
model.to("cuda")

CHUNKS_BASE_DIR = "/content/concours-de-philosophie/pipelines OCR/Pipeline_2/partitioned_chunks"
local_ocr_results = {}

page_folders = sorted(
    d for d in glob.glob(os.path.join(CHUNKS_BASE_DIR, "*"))
    if os.path.isdir(d)
)

print(f"Starting local OCR on {len(page_folders)} pages...")


def resize_if_needed(image, max_side=1400):
    """
    Shrinks the image if its longest side is larger than max_side.
    This is often the biggest memory saver for OCR/VLM models.
    """
    w, h = image.size
    longest = max(w, h)

    if longest <= max_side:
        return image

    scale = max_side / longest
    new_size = (int(w * scale), int(h * scale))

    return image.resize(new_size, Image.Resampling.LANCZOS)


# --------------------------------------------------
# OCR loop
# --------------------------------------------------

for folder in page_folders:
    page_name = os.path.basename(folder)
    print(f"Processing {page_name}...")

    chunk_files = sorted(glob.glob(os.path.join(folder, "*.png")))
    page_text_parts = []

    for chunk_path in chunk_files:
        chunk_name = os.path.basename(chunk_path)

        try:
            image = Image.open(chunk_path).convert("RGB")
            image = resize_if_needed(image, max_side=1400)

            messages = [
                {
                    "role": "user",
                    "content": [
                        # Prefer passing the PIL image if your processor supports it.
                        # If not, use {"type": "image", "url": chunk_path}
                        {"type": "image", "image": image},
                        {"type": "text", "text": "Text Recognition:"}
                    ],
                }
            ]

            inputs = processor.apply_chat_template(
                messages,
                tokenize=True,
                add_generation_prompt=True,
                return_dict=True,
                return_tensors="pt"
            )

            inputs.pop("token_type_ids", None)

            # Move tensors to device carefully
            inputs = {
                k: v.to(device, non_blocking=True) if torch.is_tensor(v) else v
                for k, v in inputs.items()
            }

            with torch.inference_mode():
                if device == "cuda":
                    with torch.autocast(device_type="cuda", dtype=torch.float16):
                        generated_ids = model.generate(
                            **inputs,
                            max_new_tokens=1024,
                            use_cache=True,
                            do_sample=False
                        )
                else:
                    generated_ids = model.generate(
                        **inputs,
                        max_new_tokens=1024,
                        use_cache=True,
                        do_sample=False
                    )

            input_len = inputs["input_ids"].shape[1]

            transcription = processor.decode(
                generated_ids[0][input_len:],
                skip_special_tokens=True
            )

            page_text_parts.append(transcription.strip())

        except torch.cuda.OutOfMemoryError as e:
            print(f"  CUDA OOM on {chunk_name}: {e}")

            if device == "cuda":
                torch.cuda.empty_cache()

        except Exception as e:
            print(f"  Error on {chunk_name}: {e}")

        finally:
            # Explicit cleanup after every chunk
            for var in ["image", "inputs", "generated_ids"]:
                if var in locals():
                    del locals()[var]

            gc.collect()

            if device == "cuda":
                torch.cuda.empty_cache()

    local_ocr_results[page_name] = "\n".join(page_text_parts)

if local_ocr_results:
    df_final = pd.DataFrame(
        list(local_ocr_results.items()),
        columns=["Page", "Texte_OCR"]
    )
```


## TXT Dump

```python
txt_path = "/content/ocr_results.txt"

with open(txt_path, "w", encoding="utf-8") as f:
    f.write(" ".join(local_ocr_results.values()))

print(f"TXT saved to: {txt_path}")
```