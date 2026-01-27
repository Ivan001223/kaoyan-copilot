from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_experimental.utilities import PythonREPL
from app.core.services.rag_engine import rag_engine
from app.core.services.ocr_engine import ocr_engine
from app.core.database.review_manager import review_manager
import os
import datetime
from typing import Optional

# --- 1. Web 搜索 ---
@tool
def web_search(query: str) -> str:
    """
    用于搜索关于大学、考试政策、招生名额的最新信息，以及与考研相关的近期新闻。
    """
    try:
        search = DuckDuckGoSearchRun()
        return search.invoke(query)
    except Exception as e:
        return f"搜索失败: {e}"

# --- 2. 数学计算器 ---
@tool
def calculator(expression: str) -> str:
    """
    用于执行复杂的数学计算。
    输入应该是一个有效的 Python 表达式字符串，例如 "123 * 456" 或 "math.sqrt(25)"。
    """
    try:
        repl = PythonREPL()
        full_code = f"import math\nprint({expression})"
        result = repl.run(full_code)
        return result.strip()
    except Exception as e:
        return f"计算失败: {e}"

# --- 3. 检索器工具 ---
@tool
def knowledge_retriever(query: str) -> str:
    """
    用于搜索关于微积分、政治、英语语法或存储在本地知识库中的任何其他材料的特定学术知识。
    """
    try:
        docs = rag_engine.retrieve_context(query)
        if not docs:
            return "知识库中未找到相关信息。"
        
        # 格式化上下文
        context_str = "\n\n".join([f"[来源: {doc.metadata.get('source', 'Unknown')}]\n{doc.page_content}" for doc in docs])
        return context_str
    except Exception as e:
        return f"检索失败: {e}"

# --- 4. 文档阅读 (OCR) ---
@tool
def read_document(file_path: str) -> str:
    """
    读取并提取文档（PDF 或图片）中的文本内容。
    当需要分析文件内容、总结文档或从图片中提取文字时使用此工具。
    
    Args:
        file_path: 文件的绝对路径。
    """
    try:
        if not os.path.exists(file_path):
            return f"错误：找不到文件 {file_path}"
            
        text = ocr_engine.process_file(file_path)
        if not text:
            return "文件内容为空或无法识别。"
        return text
    except Exception as e:
        return f"读取文件时发生错误: {str(e)}"

# --- 5. 复习管理工具 ---
@tool
def add_review_item(content: str) -> str:
    """
    将一个新的知识点或问题添加到复习队列中。
    当用户想要记住某个概念、错题或知识点时使用。
    
    Args:
        content: 需要复习的内容文本（问题或知识点）。
    """
    try:
        review_manager.add_review_task(content)
        return f"已成功添加到复习计划：{content}"
    except Exception as e:
        return f"添加失败: {str(e)}"

@tool
def get_due_reviews() -> str:
    """
    检查当前有哪些复习任务到期。
    返回需要复习的项目列表。不会自动更新复习进度。
    """
    try:
        tasks = review_manager.check_review_tasks(auto_advance_quality=None)
        if not tasks:
            return "目前没有到期的复习任务。"
        return "\n".join(tasks)
    except Exception as e:
        return f"获取复习任务失败: {str(e)}"

@tool
def submit_review_result(task_id: int, quality: int) -> str:
    """
    提交复习结果反馈。
    
    Args:
        task_id: 复习任务的 ID（从 get_due_reviews 中获取）。
        quality: 记忆质量评分，范围 0-5。
                 0=完全忘记, 3=勉强记得, 5=完美记住。
    """
    try:
        if quality < 0 or quality > 5:
            return "错误：质量评分必须在 0 到 5 之间。"
            
        return review_manager.submit_review_feedback(task_id, quality)
    except Exception as e:
        return f"提交反馈失败: {str(e)}"

# --- 6. 文件系统工具 ---
@tool
def write_file(file_path: str, content: str) -> str:
    """
    将文本内容写入指定文件。如果文件已存在，将覆盖它。
    
    Args:
        file_path: 文件的绝对路径。
        content: 要写入的文本内容。
    """
    try:
        # 确保目录存在
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"成功写入文件: {file_path}"
    except Exception as e:
        return f"写入文件失败: {str(e)}"

# --- 7. 实用工具 ---
@tool
def get_current_time() -> str:
    """
    获取当前系统时间。
    """
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

ALL_TOOLS = [
    web_search, 
    calculator, 
    knowledge_retriever,
    read_document,
    add_review_item,
    get_due_reviews,
    submit_review_result,
    write_file,
    get_current_time
]
