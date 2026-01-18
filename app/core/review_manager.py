import sqlite3
import datetime
import os
import math
from typing import List, Optional

DB_PATH = os.path.join("data", "review.db")

class ReviewManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database with SM-2 support."""
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create table if not exists (compatible with old schema)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS review_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_text TEXT NOT NULL,
                next_review_time TIMESTAMP NOT NULL,
                review_stage INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Check and add new columns for SM-2 if they don't exist
        cursor.execute("PRAGMA table_info(review_queue)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'ease_factor' not in columns:
            cursor.execute('ALTER TABLE review_queue ADD COLUMN ease_factor REAL DEFAULT 2.5')
        if 'repetitions' not in columns:
            cursor.execute('ALTER TABLE review_queue ADD COLUMN repetitions INTEGER DEFAULT 0')
        if 'interval' not in columns:
            cursor.execute('ALTER TABLE review_queue ADD COLUMN interval INTEGER DEFAULT 1')
        if 'last_reviewed_at' not in columns:
            cursor.execute('ALTER TABLE review_queue ADD COLUMN last_reviewed_at TIMESTAMP')

        conn.commit()
        conn.close()

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

    def add_review_task(self, question_text: str):
        """
        Add a question to the review queue using SM-2 defaults.
        """
        # Initial review is usually tomorrow (Stage 1 logic)
        next_review = datetime.datetime.now() + datetime.timedelta(days=1)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        # Initialize with SM-2 defaults: EF=2.5, Reps=0, Interval=1
        cursor.execute('''
            INSERT INTO review_queue (
                question_text, next_review_time, review_stage, 
                ease_factor, repetitions, interval
            )
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (question_text, next_review, 0, 2.5, 0, 1))
        conn.commit()
        conn.close()
        print(f"已添加到复习队列 (SM-2): {question_text}")

    def submit_review_feedback(self, task_id: int, quality: int):
        """
        Process user feedback and schedule next review.
        Quality: 0 (Forgot) to 5 (Perfect).
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT ease_factor, repetitions, interval FROM review_queue WHERE id = ?', (task_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return "Task not found"
            
        ease_factor, repetitions, interval = row
        # Handle defaults if NULL (migration case)
        ease_factor = ease_factor or 2.5
        repetitions = repetitions or 0
        interval = interval or 1
        
        new_ef, new_reps, new_ivl = self._calculate_next_sm2(quality, ease_factor, repetitions, interval)
        
        next_time = datetime.datetime.now() + datetime.timedelta(days=new_ivl)
        
        cursor.execute('''
            UPDATE review_queue 
            SET next_review_time = ?, ease_factor = ?, repetitions = ?, interval = ?, last_reviewed_at = ?
            WHERE id = ?
        ''', (next_time, new_ef, new_reps, new_ivl, datetime.datetime.now(), task_id))
        
        conn.commit()
        conn.close()
        return f"Review updated: Next review in {new_ivl} days (EF: {new_ef:.2f})"

    def check_review_tasks(self, auto_advance_quality: Optional[int] = 4) -> List[str]:
        """
        Check due tasks.
        Args:
            auto_advance_quality: If set (0-5), automatically updates the schedule assuming this quality.
                                  Default is 4 (Good) to maintain "reminder" behavior.
                                  Set to None to peek without rescheduling.
        """
        now = datetime.datetime.now()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, question_text, ease_factor, repetitions, interval 
            FROM review_queue
            WHERE next_review_time <= ?
        ''', (now,))
        
        due_tasks = cursor.fetchall()
        messages = []
        
        for task_id, text, ef, reps, ivl in due_tasks:
            messages.append(f"[复习时间] {text} (ID: {task_id})")
            
            if auto_advance_quality is not None:
                # Defaults for migration
                ef = ef or 2.5
                reps = reps or 0
                ivl = ivl or 1
                
                new_ef, new_reps, new_ivl = self._calculate_next_sm2(auto_advance_quality, ef, reps, ivl)
                next_time = now + datetime.timedelta(days=new_ivl)
                
                cursor.execute('''
                    UPDATE review_queue 
                    SET next_review_time = ?, ease_factor = ?, repetitions = ?, interval = ?, last_reviewed_at = ?
                    WHERE id = ?
                ''', (next_time, new_ef, new_reps, new_ivl, now, task_id))
                
        conn.commit()
        conn.close()
        
        return messages

# Singleton
review_manager = ReviewManager()
