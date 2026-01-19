import torch
import os
from typing import List, Optional, Any, Dict, Sequence, Union, Type, Callable
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool
from pydantic import BaseModel
from transformers import AutoModelForImageTextToText, AutoProcessor
from qwen_vl_utils import process_vision_info
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.language_models import BaseChatModel
from langchain_core.outputs import ChatResult, ChatGeneration, ChatGenerationChunk
from langchain_core.messages import AIMessageChunk
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from transformers import TextIteratorStreamer
from threading import Thread
from typing import Iterator

from app.core.config_manager import config_manager

class LocalQwen2VL(BaseChatModel):
    model_name: str = "Qwen/Qwen2-VL-2B-Instruct"
    model: Any = None
    processor: Any = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Update model name from config if available
        config_model = config_manager.get("local_models", "ocr_model")
        if config_model:
            self.model_name = config_model
            
        self._load_model()
        
    def _load_model(self):
        if self.model is None:
            print(f"Loading Local Qwen2-VL: {self.model_name}...")
            # Check device
            device = "cuda" if torch.cuda.is_available() else "cpu"
            dtype = torch.bfloat16 if device == "cuda" else torch.float32
            
            # Using from_pretrained with device_map
            try:
                # Use AutoModelForImageTextToText which is generic enough for Qwen2-VL and Qwen3-VL
                self.model = AutoModelForImageTextToText.from_pretrained(
                    self.model_name, 
                    torch_dtype=dtype, 
                    device_map="auto" if device == "cuda" else None,
                    trust_remote_code=True
                )
                if device == "cpu":
                    self.model = self.model.to("cpu")
                    
                self.processor = AutoProcessor.from_pretrained(self.model_name, trust_remote_code=True)
                print(f"Local Qwen2-VL loaded on {device}.")
            except Exception as e:
                print(f"Failed to load Local Qwen2-VL: {e}")
                raise e

    @property
    def _llm_type(self) -> str:
        return "local-qwen2-vl"

    def bind_tools(self, tools: Sequence[Union[Dict[str, Any], Type[BaseModel], Callable, BaseTool]], **kwargs: Any) -> Runnable:
        """
        Mock implementation of bind_tools for Local Qwen.
        """
        print("Warning: LocalQwen2VL does not support native tool binding yet. Tools ignored.")
        return self

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        # Convert LangChain messages to Qwen conversation format
        conversation = []
        
        for msg in messages:
            role = "user"
            if isinstance(msg, AIMessage):
                role = "assistant"
            elif isinstance(msg, SystemMessage):
                role = "system"
            
            content = []
            if isinstance(msg.content, str):
                content.append({"type": "text", "text": msg.content})
            elif isinstance(msg.content, list):
                # Handle multimodal content
                for item in msg.content:
                    if isinstance(item, dict):
                        if item.get("type") == "text":
                            content.append({"type": "text", "text": item.get("text")})
                        elif item.get("type") == "image_url":
                            url = item.get("image_url", {}).get("url")
                            if url:
                                content.append({"type": "image", "image": url})
            
            conversation.append({"role": role, "content": content})

        # Prepare inputs
        try:
            text = self.processor.apply_chat_template(
                conversation, tokenize=False, add_generation_prompt=True
            )
            
            image_inputs, video_inputs = process_vision_info(conversation)
            
            inputs = self.processor(
                text=[text],
                images=image_inputs,
                videos=video_inputs,
                padding=True,
                return_tensors="pt",
            )
            
            inputs = inputs.to(self.model.device)
            
            # Setup streaming
            streamer = TextIteratorStreamer(self.processor.tokenizer, skip_prompt=True, skip_special_tokens=True)
            
            # Run generation in a separate thread
            max_new_tokens = kwargs.get("max_new_tokens", 1024)
            generation_kwargs = dict(inputs, max_new_tokens=max_new_tokens, streamer=streamer)
            thread = Thread(target=self.model.generate, kwargs=generation_kwargs)
            thread.start()
            
            # Yield chunks
            for new_text in streamer:
                chunk = ChatGenerationChunk(message=AIMessageChunk(content=new_text))
                if run_manager:
                    run_manager.on_llm_new_token(new_text, chunk=chunk)
                yield chunk
                
        except Exception as e:
            print(f"Streaming failed: {e}")
            yield ChatGenerationChunk(message=AIMessageChunk(content=f"Error: {str(e)}"))

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        # Convert LangChain messages to Qwen conversation format
        conversation = []
        
        for msg in messages:
            role = "user"
            if isinstance(msg, AIMessage):
                role = "assistant"
            elif isinstance(msg, SystemMessage):
                role = "system"
            
            content = []
            if isinstance(msg.content, str):
                content.append({"type": "text", "text": msg.content})
            elif isinstance(msg.content, list):
                # Handle multimodal content
                for item in msg.content:
                    if isinstance(item, dict):
                        if item.get("type") == "text":
                            content.append({"type": "text", "text": item.get("text")})
                        elif item.get("type") == "image_url":
                            url = item.get("image_url", {}).get("url")
                            if url:
                                content.append({"type": "image", "image": url})
            
            conversation.append({"role": role, "content": content})

        # Prepare inputs
        try:
            text = self.processor.apply_chat_template(
                conversation, tokenize=False, add_generation_prompt=True
            )
            
            image_inputs, video_inputs = process_vision_info(conversation)
            
            inputs = self.processor(
                text=[text],
                images=image_inputs,
                videos=video_inputs,
                padding=True,
                return_tensors="pt",
            )
            
            inputs = inputs.to(self.model.device)

            # Generate
            with torch.no_grad():
                max_new_tokens = kwargs.get("max_new_tokens", 1024)
                generated_ids = self.model.generate(**inputs, max_new_tokens=max_new_tokens)
            
            # Trim input tokens
            generated_ids_trimmed = [
                out_ids[len(in_ids) :] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
            ]
            
            output_text = self.processor.batch_decode(
                generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
            )[0]
            
            return ChatResult(generations=[ChatGeneration(message=AIMessage(content=output_text))])
            
        except Exception as e:
            print(f"Generation failed: {e}")
            return ChatResult(generations=[ChatGeneration(message=AIMessage(content=f"Error: {str(e)}"))])

