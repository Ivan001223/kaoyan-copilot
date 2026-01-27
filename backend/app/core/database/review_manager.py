import datetime
import math
from typing import List, Optional, Dict, Any
from app.core.database.db import db_manager

class ReviewManager:
    def __init__(self):
        try:
            self._init_db()
        except Exception as e:
            print(f"Warning: ReviewManager failed to initialize DB: {e}")

    def _init_db(self):
        """Initialize MySQL tables if not exist."""
        try:
            # Create review_queue table
            create_table_query = """
            CREATE TABLE IF NOT EXISTS review_queue (
                id INT AUTO_INCREMENT PRIMARY KEY,
                question_id INT NULL,
                question_text TEXT,
                next_review_time DATETIME NOT NULL,
                review_stage INT DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                ease_factor FLOAT DEFAULT 2.5,
                repetitions INT DEFAULT 0,
                interval_days INT DEFAULT 1,
                last_reviewed_at DATETIME NULL,
                INDEX (next_review_time),
                INDEX (question_id)
            )
            """
            db_manager.execute_update(create_table_query)
        except Exception as e:
            print(f"Failed to init review db: {e}")

    def _calculate_next_sm2(self, quality: int, ease_factor: float, repetitions: int, interval: int) -> tuple[float, int, int]:
        """
        Calculate next review parameters using SuperMemo-2 algorithm.
        
        Args:
            quality: 0-5 rating (0=blackout, 5=perfect)
            ease_factor: Current ease factor (default 2.5)
            repetitions: Current successful repetition streak
            interval: Current interval in days
            
        Returns:
            (new_ease_factor, new_repetitions, new_interval)
        """
        if quality >= 3:
            # Correct response
            if repetitions == 0:
                new_interval = 1
            elif repetitions == 1:
                new_interval = 6
            else:
                new_interval = math.ceil(interval * ease_factor)
            
            new_repetitions = repetitions + 1
            new_ease_factor = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        else:
            # Incorrect response
            new_repetitions = 0
            new_interval = 1
            new_ease_factor = ease_factor # EF doesn't change on failure in some variations, or keep same
        
        if new_ease_factor < 1.3:
            new_ease_factor = 1.3
            
        return new_ease_factor, new_repetitions, new_interval

    def add_review_task(self, question_text: str, question_id: Optional[int] = None):
        """
        Add a question to the review queue using SM-2 defaults.
        """
        # Initial review is usually tomorrow (Stage 1 logic)
        next_review = datetime.datetime.now() + datetime.timedelta(days=1)
        
        query = """
            INSERT INTO review_queue (
                question_text, question_id, next_review_time, review_stage, 
                ease_factor, repetitions, interval_days
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        db_manager.execute_update(query, (question_text, question_id, next_review, 0, 2.5, 0, 1))
        print(f"Added to review queue: {question_text} (ID: {question_id})")

    def submit_review_feedback(self, task_id: int, quality: int):
        """
        Process user feedback and schedule next review.
        Quality: 0 (Forgot) to 5 (Perfect).
        """
        query = 'SELECT ease_factor, repetitions, interval_days FROM review_queue WHERE id = %s'
        results = db_manager.execute_query(query, (task_id,))
        
        if not results:
            return "Task not found"
            
        row = results[0]
        ease_factor = row.get('ease_factor') or 2.5
        repetitions = row.get('repetitions') or 0
        interval = row.get('interval_days') or 1
        
        new_ef, new_reps, new_ivl = self._calculate_next_sm2(quality, ease_factor, repetitions, interval)
        
        next_time = datetime.datetime.now() + datetime.timedelta(days=new_ivl)
        
        update_query = """
            UPDATE review_queue 
            SET next_review_time = %s, ease_factor = %s, repetitions = %s, interval_days = %s, last_reviewed_at = %s
            WHERE id = %s
        """
        db_manager.execute_update(update_query, (next_time, new_ef, new_reps, new_ivl, datetime.datetime.now(), task_id))
        
        return f"Review updated: Next review in {new_ivl} days (EF: {new_ef:.2f})"

    def get_due_reviews(self) -> List[Dict[str, Any]]:
        """Get all due review tasks."""
        now = datetime.datetime.now()
        query = """
            SELECT id, question_id, question_text, ease_factor, repetitions, interval_days 
            FROM review_queue
            WHERE next_review_time <= %s
        """
        return db_manager.execute_query(query, (now,))

    def check_review_tasks(self, auto_advance_quality: Optional[int] = 4) -> List[str]:
        """
        Check due tasks (For Agent Tool compatibility).
        Args:
            auto_advance_quality: If set (0-5), automatically updates the schedule assuming this quality.
                                  Default is 4 (Good) to maintain "reminder" behavior.
                                  Set to None to peek without rescheduling.
        """
        due_tasks = self.get_due_reviews()
        messages = []
        now = datetime.datetime.now()
        
        for task in due_tasks:
            task_id = task['id']
            text = task['question_text']
            messages.append(f"[复习时间] {text} (ID: {task_id})")
            
            if auto_advance_quality is not None:
                # Defaults for migration
                ef = task['ease_factor'] or 2.5
                reps = task['repetitions'] or 0
                ivl = task['interval_days'] or 1
                
                new_ef, new_reps, new_ivl = self._calculate_next_sm2(auto_advance_quality, ef, reps, ivl)
                next_time = now + datetime.timedelta(days=new_ivl)
                
                update_query = """
                    UPDATE review_queue 
                    SET next_review_time = %s, ease_factor = %s, repetitions = %s, interval_days = %s, last_reviewed_at = %s
                    WHERE id = %s
                """
                db_manager.execute_update(update_query, (next_time, new_ef, new_reps, new_ivl, now, task_id))
        
        return messages

# Singleton
review_manager = ReviewManager()
