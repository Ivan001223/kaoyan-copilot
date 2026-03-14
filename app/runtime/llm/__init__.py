from langchain_openai import ChatOpenAI
from app.infrastructure.config.settings import settings

_local_qwen_instance = None

def get_local_qwen_provider():
    """
    Directly access the Local Qwen instance (Singleton).
    Initializes it if not already done.
    """
    global _local_qwen_instance
    if _local_qwen_instance is None:
        from app.core.llm.local_qwen import LocalQwen2VL
        _local_qwen_instance = LocalQwen2VL()
    return _local_qwen_instance

def get_llm(temperature: float = 0, streaming: bool = True, json_mode: bool = False):
    """
    统一获取配置好的 LLM 实例。
    """
    global _local_qwen_instance
    llm_config = settings.llm
    model_name = llm_config.model

    if model_name == "local-qwen2-vl":
        return get_local_qwen_provider()

    model_kwargs = {}
    if json_mode:
        model_kwargs["response_format"] = {"type": "json_object"}

    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        base_url=llm_config.base_url,
        api_key=llm_config.api_key,
        streaming=streaming,
        model_kwargs=model_kwargs
    )
