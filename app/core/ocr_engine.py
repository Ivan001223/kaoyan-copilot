import os
import torch
import tempfile
from transformers import AutoModel, AutoTokenizer
from PIL import Image
from pdf2image import convert_from_path
from typing import List, Union

class DeepSeekOCR:
    _instance = None
    _model = None
    _tokenizer = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DeepSeekOCR, cls).__new__(cls)
        return cls._instance

    def _load_model(self):
        if self._model is None:
            # 1. Try env var path
            # 2. Fallback to HF Hub ID
            model_path = os.getenv("MODEL_PATH_OCR")
            if not model_path or not os.path.exists(model_path):
                 print(f"Local model path not found: {model_path}, using HF Hub ID.")
                 model_path = "deepseek-ai/DeepSeek-OCR"
            
            print(f"Loading DeepSeek-OCR model from: {model_path} ...")
            
            try:
                self._tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
                
                # Determine device
                device = "cpu"
                dtype = torch.float32
                if torch.cuda.is_available():
                    device = "cuda"
                    dtype = torch.bfloat16
                elif torch.backends.mps.is_available():
                    device = "mps"
                    dtype = torch.float16 # MPS often prefers float16
                
                self._model = AutoModel.from_pretrained(
                    model_path, 
                    trust_remote_code=True, 
                    torch_dtype=dtype
                )
                self._model = self._model.to(device)
                self._model.eval()
                print(f"DeepSeek-OCR model loaded on {device}")
            except Exception as e:
                print(f"Failed to load DeepSeek-OCR: {e}")
                raise e

    def process_file(self, file_path: str) -> str:
        """
        Process a PDF or Image file and return the extracted text using DeepSeek-OCR.
        """
        self._load_model()
        ext = os.path.splitext(file_path)[1].lower()
        
        images = []
        temp_files = []
        
        try:
            if ext == '.pdf':
                images = convert_from_path(file_path)
            elif ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp']:
                # For single images, we can just use the path directly in the infer call
                # unless we need to preprocess.
                pass 
            else:
                # Unsupported format for OCR, return empty or raise
                return ""

            full_text = []
            
            # Helper to run inference
            def run_inference(img_path):
                prompt = "<image>\n<|grounding|>Convert the document to markdown. "
                # The infer method signature from documentation:
                # infer(self, tokenizer, prompt='', image_file='', output_path=' ', ...)
                res = self._model.infer(
                    self._tokenizer,
                    prompt=prompt,
                    image_file=img_path,
                    crop_mode=True
                )
                return res

            if ext == '.pdf':
                for i, img in enumerate(images):
                    # Save page to temp file
                    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False, mode='wb') as tmp:
                        img.save(tmp.name)
                        temp_files.append(tmp.name)
                        res = run_inference(tmp.name)
                        full_text.append(res)
            else:
                # Single image file
                res = run_inference(file_path)
                full_text.append(res)
                
            return "\n\n".join(full_text)
            
        finally:
            # Cleanup temp files
            for p in temp_files:
                if os.path.exists(p):
                    os.remove(p)

ocr_engine = DeepSeekOCR()
