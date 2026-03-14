import os
from typing import List
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda, RunnableParallel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from app.runtime.graph.state import AgentState
from app.runtime.llm import get_llm
from app.skills.rag.rag_engine import rag_engine
from app.infrastructure.utils.image_handler import process_multimodal_content

VECTOR_STORE_PATH = os.path.join("data", "vector_store")

def get_tutor_node():
    """
    返回 Tutor Agent 的 LangGraph 节点（可调用对象）。
    """
    retriever = RunnableLambda(lambda q: rag_engine.retrieve_context(q, k=3))

    template = """你是一位考研全科助教，采用苏格拉底（Socratic Maieutics）进行教学。

    重要规则：
    1. **严禁**直接给出最终答案或完整解析。
    2. 必须使用简体中文回答。
    3. 首先分析用户的问题。
    4. 提出引导性问题帮助用户思考（例如："你觉得这里应该用什么公式？"或"第一步是什么？"）。
    5. 只有在用户尝试后仍然卡住时，才提供下一步的提示。
    6. 数学公式**必须**包含在美元符号中，例如：$E = mc^2$ 或 $$x^2$$。
    7. 如果题目来自图片 OCR，请仔细核对数字和选项。OCR 经常会错误地翻转分数（例如将 5/2 识别为 2/5）。如果你的计算结果是 X，而选项中有 1/X 或类似的翻转形式，请指出这可能是 OCR 错误，并以你的计算为准，提示用户查看原图确认。

    上下文：
    {context}

    问题：
    {question}
    """
    prompt = ChatPromptTemplate.from_template(template)

    llm = get_llm(temperature=0)

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    rag_chain_with_source = RunnableParallel({
        "context": retriever,
        "question": RunnablePassthrough()
    }).assign(answer=(
        RunnablePassthrough.assign(
            context=lambda x: format_docs(x["context"])
        )
        | prompt
        | llm
        | StrOutputParser()
    ))

    def tutor_node(state: AgentState):
        messages = state['messages']
        last_message = messages[-1]

        raw_content = last_message.content
        question_text = ""

        if isinstance(raw_content, list):
             text_parts = [item.get('text', '') for item in raw_content if item.get('type') == 'text']
             question_text = " ".join(text_parts)
        else:
             question_text = raw_content

        context_docs = retriever.invoke(question_text)
        formatted_context = format_docs(context_docs)

        sys_msg_content = template.replace("{context}", formatted_context).replace("{question}", "")
        sys_msg_content = sys_msg_content.replace("问题：\n", "")

        messages_to_send = [SystemMessage(content=sys_msg_content)]

        if isinstance(raw_content, list):
             processed_content = process_multimodal_content(raw_content)
             messages_to_send.append(HumanMessage(content=processed_content))
        else:
             messages_to_send.append(HumanMessage(content=question_text))

        response_msg = llm.invoke(messages_to_send)
        response = response_msg.content

        sources = []
        for doc in context_docs:
            if "source" in doc.metadata:
                file_path = doc.metadata["source"]
                filename = os.path.basename(file_path)
                url = f"http://localhost:8000/files/{filename}"
                sources.append({
                    "title": filename,
                    "url": url,
                    "content": doc.page_content[:100] + "..."
                })

        unique_sources = []
        seen_urls = set()
        for s in sources:
            if s["url"] not in seen_urls:
                unique_sources.append(s)
                seen_urls.add(s["url"])

        return {"messages": [AIMessage(content=response, additional_kwargs={"sources": unique_sources})]}

    return tutor_node
