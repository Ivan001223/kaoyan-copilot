import os
from typing import List
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
# ChromaDB 持久化路径
VECTOR_STORE_PATH = os.path.join("data", "vector_store")

from app.core.state import AgentState

def get_tutor_node():
    """
    返回 Tutor Agent 的 LangGraph 节点（可调用对象）。
    """
    # 初始化向量存储（从磁盘加载）
    # 必须与 RAGEngine 使用相同的 Embeddings


    # 使用 RAGEngine 进行检索（包含 Rerank）
    from app.core.rag_engine import rag_engine
    from langchain_core.runnables import RunnableLambda

    # 包装 retrieve_context 为 Runnable
    retriever = RunnableLambda(lambda q: rag_engine.retrieve_context(q, k=3))

    # 定义提示模板
    template = """你是一位考研全科助教，采用苏格拉底（Socratic Maieutics）进行教学。
    
    重要规则：
    1. **严禁**直接给出最终答案或完整解析。
    2. 必须使用简体中文回答。
    3. 首先分析用户的问题。
    4. 提出引导性问题帮助用户思考（例如：“你觉得这里应该用什么公式？”或“第一步是什么？”）。
    5. 只有在用户尝试后仍然卡住时，才提供下一步的提示。
    6. 数学公式请使用 LaTeX 格式：$E = mc^2$。
    
    上下文：
    {context}
    
    问题：
    {question}
    """
    prompt = ChatPromptTemplate.from_template(template)
    
    # 初始化 LLM
    from app.core.config_manager import config_manager
    llm_config = config_manager.get_config().get("llm", {})

    llm = ChatOpenAI(
        model=llm_config.get("model", "gpt-4o"),
        temperature=0,
        base_url=llm_config.get("base_url"),
        api_key=llm_config.get("api_key")
    )

    # RAG 链
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    # 节点函数
    def tutor_node(state: AgentState):
        messages = state['messages']
        last_message = messages[-1]
        question = last_message.content
        
        response = rag_chain.invoke(question)
        
        # 将响应作为消息更新返回
        #Follow LangGraph 模式：返回一个包含要追加的 'messages' 键的字典
        from langchain_core.messages import AIMessage
        return {"messages": [AIMessage(content=response)]}

    return tutor_node
