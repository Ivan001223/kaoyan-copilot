import os
import sys
from app.core.config.config_manager import config_manager

try:
    from modelscope import snapshot_download
except ImportError:
    snapshot_download = None

def check_and_download_models():
    """
    Check if configured local models exist. 
    If not, attempt to download them using ModelScope.
    Updates the configuration with the local paths of the downloaded models.
    """
    print("--- Checking Local Models Availability ---")
    
    if snapshot_download is None:
        print("Warning: 'modelscope' library not found. Skipping auto-download.")
        print("Install it with: pip install modelscope")
        return

    local_models_config = config_manager.get_config().get("local_models", {})
    updated_models = {}
    needs_update = False

    # Define the keys we care about
    model_keys = ["ocr_model", "embedding_model", "rerank_model"]

    for key in model_keys:
        model_id = local_models_config.get(key)
        if not model_id:
            continue

        # 1. Check if it's already a valid local path
        if os.path.isdir(model_id) or os.path.isfile(model_id):
            print(f"✅ Model '{key}' found locally: {model_id}")
            continue

        # 2. Not a local path, assume it's a Model ID and try to download
        print(f"⬇️  Model '{key}' ({model_id}) not found locally. Attempting download via ModelScope...")
        
        try:
            # snapshot_download returns the local cache directory path
            # We map the HF ID to ModelScope ID if necessary, or assume they are the same.
            # Most Qwen models are on ModelScope with similar IDs.
            
            # Note: DavidWen2025/Qwen3-VL-8B-Instruct-4bit-GPTQ might be a HF specific ID.
            # If ModelScope doesn't have it, this will fail. 
            # Ideally we would have a mapping, but we'll try the ID as is first.
            
            model_dir = snapshot_download(model_id)
            print(f"✅ Downloaded '{key}' to: {model_dir}")
            
            updated_models[key] = model_dir
            needs_update = True
            
        except Exception as e:
            print(f"❌ Failed to download '{model_id}' from ModelScope: {e}")
            print("   The system will attempt to load it using the original ID (likely from Hugging Face).")
            # We don't update the config, so it stays as the ID
            pass

    # 3. Update config if we downloaded anything
    if needs_update:
        print("Updating configuration with local model paths...")
        # We merge the existing local_models config with our updates
        new_local_models = local_models_config.copy()
        new_local_models.update(updated_models)
        
        # Save via config manager
        config_manager.update_config({"local_models": new_local_models})
        print("Configuration updated.")

    print("--- Model Check Complete ---")
