import os
import torch
from typing import List, Any
from langchain_core.embeddings import Embeddings
from transformers import AutoModel, AutoProcessor

class Qwen3VLEmbeddings(Embeddings):
    """
    Wrapper for Qwen3-VL-Embedding-2B model.
    """
    def __init__(self, model_name: str = None):
        # 1. Try env var path
        # 2. Fallback to passed arg
        # 3. Fallback to HF Hub ID
        
        env_path = os.getenv("MODEL_PATH_EMBEDDING")
        if env_path and os.path.exists(env_path):
             self.model_name = env_path
        else:
             self.model_name = model_name or "Qwen/Qwen3-VL-Embedding-2B"
             
        self._model = None
        self._processor = None
        self._device = self._get_device()

    def _get_device(self) -> str:
        if torch.cuda.is_available():
            return "cuda"
        elif torch.backends.mps.is_available():
            return "mps"
        return "cpu"

    def _load_model(self):
        if self._model is None:
            print(f"Loading Embedding Model: {self.model_name} on {self._device}...")
            try:
                # Use trust_remote_code=True as these are new models
                self._model = AutoModel.from_pretrained(
                    self.model_name,
                    trust_remote_code=True,
                    torch_dtype=torch.float16 if self._device != "cpu" else torch.float32
                ).to(self._device)
                
                self._processor = AutoProcessor.from_pretrained(
                    self.model_name, 
                    trust_remote_code=True
                )
                self._model.eval()
                print("Embedding Model Loaded.")
            except Exception as e:
                print(f"Error loading embedding model: {e}")
                raise e

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        self._load_model()
        results = []
        for text in texts:
            results.append(self._embed_single(text))
        return results

    def embed_query(self, text: str) -> List[float]:
        self._load_model()
        return self._embed_single(text)

    def _embed_single(self, text: str) -> List[float]:
        try:
            # Qwen-VL processing
            inputs = self._processor(text=[text], return_tensors="pt", padding=True)
            inputs = {k: v.to(self._device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self._model(**inputs)
                
                # Check if the model returns 'embedding' or 'text_embeds' directly
                if hasattr(outputs, 'text_embeds'):
                     return outputs.text_embeds[0].float().cpu().tolist()
                
                # If not, use last hidden state logic for Causal LM
                last_hidden_state = outputs.last_hidden_state
                
                if 'attention_mask' in inputs:
                    mask = inputs['attention_mask']
                    # mask.sum(dim=1) gives the length (assuming padding is 0 and at the end or beginning handled correctly)
                    # We want the index of the last token.
                    last_indices = mask.sum(dim=1) - 1
                    embedding = last_hidden_state[0, last_indices[0], :]
                else:
                    embedding = last_hidden_state[0, -1, :]
                    
                return embedding.float().cpu().tolist()
        except Exception as e:
            print(f"Embedding error for text '{text[:20]}...': {e}")
            # Return zero vector fallback or re-raise
            raise e
