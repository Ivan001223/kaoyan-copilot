import json
import datetime
from typing import List, Dict, Any, Optional
from app.core.database.db import db_manager
from app.core.database.review_manager import review_manager

class QuestionManager:
    def __init__(self):
        try:
            self._init_db()
        except Exception as e:
            print(f"Warning: QuestionManager failed to initialize DB: {e}")

    def _init_db(self):
        try:
            # Questions table
            # options and tags are stored as JSON strings
            q_table = """
            CREATE TABLE IF NOT EXISTS questions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                content TEXT NOT NULL,
                type VARCHAR(50),
                options JSON, 
                answer TEXT,
                explanation TEXT,
                subject VARCHAR(50),
                year INT,
                source VARCHAR(100),
                tags JSON,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX (subject),
                INDEX (year),
                INDEX (type)
            )
            """
            db_manager.execute_update(q_table)

            # User Answers table
            ua_table = """
            CREATE TABLE IF NOT EXISTS user_answers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(100),
                question_id INT,
                selected_option TEXT,
                is_correct BOOLEAN,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX (user_id),
                INDEX (question_id)
            )
            """
            db_manager.execute_update(ua_table)
            
        except Exception as e:
            print(f"Failed to init question db: {e}")

    def get_questions(self, subject: Optional[str] = None, year: Optional[int] = None, 
                      limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        conditions = []
        params = []
        
        if subject:
            conditions.append("subject = %s")
            params.append(subject)
        if year:
            conditions.append("year = %s")
            params.append(year)
            
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        query = f"""
            SELECT * FROM questions 
            {where_clause}
            ORDER BY year DESC, id ASC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        
        results = db_manager.execute_query(query, tuple(params))
        
        # Parse JSON fields
        for r in results:
            if isinstance(r.get('options'), str):
                try:
                    r['options'] = json.loads(r['options'])
                except:
                    pass
            if isinstance(r.get('tags'), str):
                try:
                    r['tags'] = json.loads(r['tags'])
                except:
                    pass
                
        return results

    def get_question_by_id(self, q_id: int) -> Optional[Dict[str, Any]]:
        results = db_manager.execute_query("SELECT * FROM questions WHERE id = %s", (q_id,))
        if not results:
            return None
        r = results[0]
        if isinstance(r.get('options'), str):
            try:
                r['options'] = json.loads(r['options'])
            except:
                pass
        if isinstance(r.get('tags'), str):
            try:
                r['tags'] = json.loads(r['tags'])
            except:
                pass
        return r

    def submit_answer(self, user_id: str, question_id: int, selected_option: str) -> Dict[str, Any]:
        """
        Submit an answer, check correctness, log it, and add to error book if wrong.
        """
        # 1. Get correct answer
        q = self.get_question_by_id(question_id)
        if not q:
            raise ValueError("Question not found")
            
        # Normalize comparison (strip spaces, case insensitive for letters)
        correct_answer = str(q['answer']).strip()
        user_answer = str(selected_option).strip()
        
        is_correct = (user_answer.lower() == correct_answer.lower())
        
        # 2. Log user answer
        insert_query = """
            INSERT INTO user_answers (user_id, question_id, selected_option, is_correct)
            VALUES (%s, %s, %s, %s)
        """
        db_manager.execute_update(insert_query, (user_id, question_id, selected_option, is_correct))
        
        # 3. If wrong, add to Review Manager (Error Notebook)
        if not is_correct:
            # Add to review queue
            review_manager.add_review_task(q['content'][:100] + "...", question_id=question_id)
            
        return {
            "is_correct": is_correct,
            "correct_answer": q['answer'],
            "explanation": q['explanation']
        }

    def get_radar_stats(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Calculate accuracy per tag (Knowledge Point).
        Returns: [{ subject: 'Math', tag: 'Calculus', total: 10, correct: 6, score: 60 }, ...]
        """
        # Join user_answers with questions to get tags
        query = """
            SELECT q.subject, q.tags, ua.is_correct
            FROM user_answers ua
            JOIN questions q ON ua.question_id = q.id
            WHERE ua.user_id = %s
        """
        results = db_manager.execute_query(query, (user_id,))
        
        stats = {} # Key: (subject, tag) -> {total, correct}
        
        for r in results:
            subject = r['subject']
            tags = r['tags']
            if isinstance(tags, str):
                try:
                    tags = json.loads(tags)
                except:
                    tags = []
            elif tags is None:
                tags = []
            
            is_correct = 1 if r['is_correct'] else 0
            
            for tag in tags:
                key = (subject, tag)
                if key not in stats:
                    stats[key] = {"total": 0, "correct": 0}
                stats[key]["total"] += 1
                stats[key]["correct"] += is_correct
                
        # Format output
        output = []
        for (subj, tag), data in stats.items():
            if data["total"] > 0:
                score = int((data["correct"] / data["total"]) * 100)
                output.append({
                    "subject": subj,
                    "tag": tag,
                    "total": data["total"],
                    "correct": data["correct"],
                    "score": score
                })
            
        return output

    def get_similar_questions(self, question_id: int, limit: int = 3) -> List[Dict[str, Any]]:
        """
        Find questions with overlapping tags to the given question (excluding itself).
        """
        q = self.get_question_by_id(question_id)
        if not q:
            return []
            
        tags = q['tags']
        if not tags:
            return []
            
        # This is a basic tag matching implementation.
        first_tag = tags[0] if len(tags) > 0 else ""
        
        # Safe query
        query = """
            SELECT * FROM questions 
            WHERE subject = %s AND id != %s
            LIMIT 50
        """
        results = db_manager.execute_query(query, (q['subject'], question_id))
        
        # Parse and sort by number of matching tags in Python
        scored = []
        for r in results:
            if isinstance(r.get('options'), str):
                try:
                    r['options'] = json.loads(r['options'])
                except:
                    pass
            if isinstance(r.get('tags'), str):
                try:
                    r['tags'] = json.loads(r['tags'])
                except:
                    pass
            
            r_tags = set(r['tags'] if r['tags'] else [])
            q_tags = set(tags)
            overlap = len(r_tags.intersection(q_tags))
            
            # Bonus for same type
            if r['type'] == q['type']:
                overlap += 0.5
                
            if overlap > 0:
                scored.append((overlap, r))
            
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:limit]]

question_manager = QuestionManager()
