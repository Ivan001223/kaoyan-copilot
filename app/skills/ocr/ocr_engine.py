import os
import tempfile
import traceback
from pdf2image import convert_from_path
from typing import List
from app.core.llm.llm_factory import get_local_qwen_provider
from langchain_core.messages import HumanMessage

from app.infrastructure.config import settings


class QwenVLOCR:
    def process_file(self, file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()

        try:
            llm = get_local_qwen_provider()
        except Exception as e:
            print(f"Failed to get Qwen-VL provider: {e}")
            return ""

        full_text = []
        temp_files = []

        try:
            images_paths = []
            if ext == '.pdf':
                try:
                    images = convert_from_path(file_path)
                except Exception as e:
                    print(f"PDF conversion failed: {e}")
                    return ""

                for img in images:
                    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False, mode='wb') as tmp:
                        img.save(tmp.name)
                        temp_files.append(tmp.name)
                        images_paths.append(tmp.name)
            elif ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp']:
                images_paths = [file_path]
            else:
                print(f"Unsupported file type for OCR: {ext}")
                return ""

            print(f"OCR Processing {len(images_paths)} images with Qwen2-VL...")

            for i, img_path in enumerate(images_paths):
                abs_path = os.path.abspath(img_path).replace("\\", "/")
                image_url = f"file://{abs_path}"

                message = HumanMessage(
                    content=[
                        {"type": "image_url", "image_url": {"url": image_url}},
                        {"type": "text", "text": "Please transcribe all the text in this image accurately. Preserve the layout and structure as much as possible. Do not add any conversational filler. If there are mathematical formulas, output them in LaTeX format."}
                    ]
                )

                print(f"  - Processing image {i+1}/{len(images_paths)}...")
                response = llm.invoke([message], max_new_tokens=2048)
                text = response.content
                full_text.append(text)

            return "\n\n".join(full_text)

        except Exception as e:
            print(f"OCR Error: {e}")
            traceback.print_exc()
            return ""
        finally:
            for p in temp_files:
                if os.path.exists(p):
                    try:
                        os.remove(p)
                    except:
                        pass


ocr_engine = QwenVLOCR()
