import os
import torch
from transformers import AutoModel, AutoProcessor
from typing import List, Tuple, Any

class Qwen3VLReranker:
    def __init__(self, model_name: str = None):
        # 1. Try env var path
        # 2. Fallback to passed arg
        # 3. Fallback to HF Hub ID
        
        env_path = os.getenv("MODEL_PATH_RERANKER")
        if env_path and os.path.exists(env_path):
             self.model_name = env_path
        else:
             self.model_name = model_name or "Qwen/Qwen3-VL-Reranker-2B"
             
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
            print(f"Loading Reranker Model: {self.model_name} on {self._device}...")
            try:
                self._model = AutoModel.from_pretrained(
                    self.model_name,
                    trust_remote_code=True,
                    torch_dtype=torch.float16 if self._device != "cpu" else torch.float32
                ).to(self._device)
                
                # Processor might not be strictly needed if compute_score handles it, 
                # but good to have if we need to manually process.
                try:
                    self._processor = AutoProcessor.from_pretrained(
                        self.model_name,
                        trust_remote_code=True
                    )
                except:
                    pass
                    
                self._model.eval()
                print("Reranker Model Loaded.")
            except Exception as e:
                print(f"Failed to load Reranker: {e}")
                raise e

    def rerank(self, query: str, documents: List[str], top_k: int = 3) -> List[Tuple[str, float, int]]:
        """
        Rerank a list of documents based on the query.
        Returns list of (doc_content, score, original_index) sorted by score.
        """
        if not documents:
            return []
            
        self._load_model()
        scores = []
        
        # Prepare pairs
        pairs = [[query, doc] for doc in documents]
        
        try:
            # Check for standard reranker methods provided by custom model code
            if hasattr(self._model, 'compute_score'):
                with torch.no_grad():
                    # compute_score usually takes a list of [query, doc]
                    batch_scores = self._model.compute_score(pairs)
                    
                    if isinstance(batch_scores, torch.Tensor):
                        batch_scores = batch_scores.cpu().tolist()
                    elif isinstance(batch_scores, list):
                        pass
                    else:
                        # Maybe it returns a dict?
                        pass
                        
                    for i, score in enumerate(batch_scores):
                        scores.append((documents[i], float(score), i))
                        
            elif hasattr(self._model, 'predict'):
                 # Some use predict
                 batch_scores = self._model.predict(pairs)
                 for i, score in enumerate(batch_scores):
                    scores.append((documents[i], float(score), i))
            else:
                print("Warning: Reranker model does not have 'compute_score' or 'predict'. Using fallback (no reranking).")
                # Fallback: return original order with 0 score
                return [(doc, 0.0, i) for i, doc in enumerate(documents)][:top_k]

            # Sort by score descending
            scores.sort(key=lambda x: x[1], reverse=True)
            return scores[:top_k]
            
        except Exception as e:
            print(f"Reranking failed: {e}")
            # Fallback
            return [(doc, 0.0, i) for i, doc in enumerate(documents)][:top_k]
