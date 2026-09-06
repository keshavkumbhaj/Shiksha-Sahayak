import os
import cv2
import torch
from PIL import Image
from ultralytics import YOLO
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

# =====================================================================
# 1. SETUP PATHS & CONFIGURATION
# =====================================================================
CUSTOM_YOLO_PATH = r"C:\Users\Ankit\OneDrive\Documents\work.py\runs\detect\train-29\weights\best.pt"
IMAGE_INPUT_PATH = r"C:\Users\Ankit\OneDrive\Documents\test.png"
VISION_MODEL_ID = "Qwen/Qwen2.5-VL-3B-Instruct"

if not os.path.exists(CUSTOM_YOLO_PATH):
    raise FileNotFoundError(f"Could not locate YOLO model at: {CUSTOM_YOLO_PATH}")

if not os.path.exists(IMAGE_INPUT_PATH):
    raise FileNotFoundError(f"Could not locate target image at: {IMAGE_INPUT_PATH}")

# =====================================================================
# 2. INITIALIZE MODELS
# =====================================================================
print("🚀 Initializing YOLO and Qwen 2.5 VL models...")

# Load custom YOLO model
yolo_model = YOLO(CUSTOM_YOLO_PATH)

# Load Qwen2.5-VL processor and model
processor = AutoProcessor.from_pretrained(VISION_MODEL_ID)
model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
    VISION_MODEL_ID,
    device_map="auto",
    torch_dtype=torch.bfloat16
)

# =====================================================================
# 3. RUN YOLO OBJECT DETECTION
# =====================================================================
print("🎯 Detecting questions in the image...")
img_bgr = cv2.imread(r"C:\Users\Ankit\OneDrive\Documents\test.png")
yolo_results = yolo_model(img_bgr, conf=0.25)

boxes = yolo_results[0].boxes

# =====================================================================
# 4. PROCESS DETECTIONS & SOLVE QUESTIONS
# =====================================================================
if len(boxes) == 0:
    print("❌ No questions detected by YOLO in the image.")
else:
    # Convert base image to PIL RGB format for accurate cropping
    original_pil = Image.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))
    print(f"📊 Found {len(boxes)} question(s). Starting transcription and solving...\n")

    for idx, box in enumerate(boxes):
        # Extract coordinates [x1, y1, x2, y2]
        coords = box.xyxy[0].cpu().numpy().astype(int)
        cropped_question_img = original_pil.crop(
            (coords[0], coords[1], coords[2], coords[3])
        )

        # Optional: Save cropped region to disk for debugging
        debug_crop_path = f"debug_crop_{idx + 1}.png"
        cropped_question_img.save(debug_crop_path)

        # Prepare chat prompt for Qwen
        prompt = (
            "You are a helpful tutor. Read the question inside this image and "
            "provide the correct, detailed step-by-step answer in English."
        )

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": cropped_question_img},
                    {"type": "text", "text": prompt}
                ]
            }
        ]

        # Apply chat template and build tensors
        text = processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        inputs = processor(
            text=[text],
            images=[cropped_question_img],
            padding=True,
            return_tensors="pt"
        ).to(model.device)

        # Generate output tokens
        with torch.no_grad():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=512,
                do_sample=False
            )

        # Decode tokens to string
        generated_ids = [
            output_ids[i][len(inputs.input_ids[i]):]
            for i in range(len(output_ids))
        ]
        answer = processor.batch_decode(
            generated_ids,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False
        )[0]

        print(f"================== Question #{idx + 1} ==================")
        print(f"Crop saved: {debug_crop_path}")
        print(f"Answer:\n{answer}\n")