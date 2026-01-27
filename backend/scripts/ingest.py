import os
import argparse
from app.core.services.rag_engine import rag_engine

def main():
    parser = argparse.ArgumentParser(description="将 PDF 文件摄取到 Kaoyan Copilot 向量存储中。")
    parser.add_argument("pdf_path", help="要摄取的 PDF 文件的路径。")
    
    args = parser.parse_args()
    
    pdf_path = args.pdf_path
    
    if not os.path.exists(pdf_path):
        print(f"错误: 找不到文件 '{pdf_path}'。")
        return
        
    print(f"正在摄取 '{pdf_path}'...")
    try:
        rag_engine.add_knowledge_base(pdf_path)
        print("完成！")
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    main()
