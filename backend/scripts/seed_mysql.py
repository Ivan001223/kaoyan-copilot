import sys
import os
import json
import random

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database.db import db_manager
from app.core.database.question_manager import question_manager # Forces table init

def seed_data():
    print("Starting data seeding...")
    
    # 1. Politics Questions
    politics_questions = [
        {
            "content": "马克思主义中国化的第一次历史性飞跃是（ ）",
            "type": "single_choice",
            "options": ["A. 毛泽东思想", "B. 邓小平理论", "C. '三个代表'重要思想", "D. 科学发展观"],
            "answer": "A",
            "explanation": "毛泽东思想是马克思主义中国化的第一次历史性飞跃。",
            "subject": "politics",
            "year": 2015,
            "source": "真题",
            "tags": ["毛泽东思想", "马克思主义中国化"]
        },
        {
            "content": "下列属于唯物辩证法基本范畴的是（ ）",
            "type": "multi_choice",
            "options": ["A. 原因与结果", "B. 必然性与偶然性", "C. 可能性与现实性", "D. 现象与本质"],
            "answer": "ABCD",
            "explanation": "唯物辩证法五对范畴：原因与结果、必然性与偶然性、可能性与现实性、现象与本质、内容与形式。",
            "subject": "politics",
            "year": 2018,
            "source": "模拟题",
            "tags": ["唯物辩证法", "哲学范畴"]
        },
        {
            "content": "中共八大提出，社会主义改造基本完成后，我国社会的主要矛盾是（ ）",
            "type": "single_choice",
            "options": ["A. 无产阶级同资产阶级之间的矛盾", "B. 人民对于经济文化迅速发展的需要同当前经济文化不能满足人民需要的状况之间的矛盾", "C. 社会主义道路与资本主义道路的矛盾", "D. 生产关系与生产力的矛盾"],
            "answer": "B",
            "explanation": "中共八大正确分析了国内主要矛盾的变化。",
            "subject": "politics",
            "year": 2012,
            "source": "真题",
            "tags": ["中共八大", "主要矛盾"]
        },
        {
             "content": "新民主主义革命的动力包括（ ）",
             "type": "multi_choice",
             "options": ["A. 工人阶级", "B. 农民阶级", "C. 城市小资产阶级", "D. 民族资产阶级"],
             "answer": "ABCD",
             "explanation": "新民主主义革命的动力是工人、农民、城市小资产阶级和民族资产阶级。",
             "subject": "politics",
             "year": 2010,
             "source": "真题",
             "tags": ["新民主主义革命", "毛泽东思想"]
        }
    ]

    # 2. Math Questions
    math_questions = [
        {
            "content": "Lim(x->0) (sin x / x) = ?",
            "type": "single_choice",
            "options": ["A. 0", "B. 1", "C. ∞", "D. Does not exist"],
            "answer": "B",
            "explanation": "重要极限之一。",
            "subject": "math",
            "year": 2010,
            "source": "基础题",
            "tags": ["极限", "微积分"]
        },
        {
            "content": "设A为3阶方阵，|A|=2，则|2A|=（ ）",
            "type": "single_choice",
            "options": ["A. 4", "B. 8", "C. 16", "D. 2"],
            "answer": "C",
            "explanation": "|kA| = k^n * |A|，这里 n=3，k=2，所以 |2A| = 2^3 * 2 = 8 * 2 = 16。",
            "subject": "math",
            "year": 2019,
            "source": "真题",
            "tags": ["线性代数", "行列式"]
        },
        {
            "content": "函数 f(x) = x^3 - 3x 在区间 [-2, 2] 上的最大值是（ ）",
            "type": "single_choice",
            "options": ["A. 2", "B. -2", "C. 18", "D. 0"],
            "answer": "A",
            "explanation": "求导 f'(x)=3x^2-3，令f'(x)=0得x=±1。f(1)=-2, f(-1)=2, f(2)=2, f(-2)=-2。最大值为2。",
            "subject": "math",
            "year": 2021,
            "source": "模拟题",
            "tags": ["导数", "最值", "微积分"]
        },
        {
            "content": "若向量 a=(1,2,3), b=(x,4,6) 共线，则 x = ( )",
            "type": "single_choice",
            "options": ["A. 1", "B. 2", "C. 3", "D. 0.5"],
            "answer": "B",
            "explanation": "对应分量成比例：1/x = 2/4 = 3/6，解得 x=2。",
            "subject": "math",
            "year": 2015,
            "source": "基础题",
            "tags": ["线性代数", "向量"]
        }
    ]

    # 3. English Questions
    english_questions = [
        {
            "content": "The word 'precarious' in the text is closest in meaning to ( )",
            "type": "single_choice",
            "options": ["A. stable", "B. uncertain", "C. precious", "D. precise"],
            "answer": "B",
            "explanation": "Precarious means not securely held or in position; dangerously likely to fall or collapse. Uncertain is the closest synonym.",
            "subject": "english",
            "year": 2016,
            "source": "Reading Comprehension",
            "tags": ["Vocabulary", "Reading"]
        },
        {
            "content": "He ______ have finished the work by now, but he is still working on it.",
            "type": "single_choice",
            "options": ["A. must", "B. should", "C. can", "D. need"],
            "answer": "B",
            "explanation": "'Should have done' indicates something that was expected to happen but didn't.",
            "subject": "english",
            "year": 2014,
            "source": "Grammar",
            "tags": ["Grammar", "Modal Verbs"]
        },
        {
            "content": "Which of the following is NOT true according to the passage?",
            "type": "single_choice",
            "options": ["A. Technology changes society.", "B. AI is dangerous.", "C. People fear change.", "D. History repeats itself."],
            "answer": "B",
            "explanation": "Inferred from context (Mock Question).",
            "subject": "english",
            "year": 2023,
            "source": "Mock",
            "tags": ["Reading", "Inference"]
        }
    ]

    all_questions = politics_questions + math_questions + english_questions

    count = 0
    for q in all_questions:
        try:
            # Check for duplicates first? Nah, just insert.
            query = """
                INSERT INTO questions (content, type, options, answer, explanation, subject, year, source, tags)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            db_manager.execute_update(query, (
                q['content'],
                q['type'],
                json.dumps(q['options'], ensure_ascii=False),
                q['answer'],
                q['explanation'],
                q['subject'],
                q['year'],
                q['source'],
                json.dumps(q['tags'], ensure_ascii=False)
            ))
            count += 1
        except Exception as e:
            print(f"Error inserting question: {e}")

    print(f"Successfully seeded {count} questions.")

if __name__ == "__main__":
    seed_data()
