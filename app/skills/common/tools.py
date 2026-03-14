import json
import re
from typing import Any, Dict, List, Optional


class Tool:
    def __init__(self, name: str, description: str, parameters: Dict[str, Any]):
        self.name = name
        self.description = description
        self.parameters = parameters

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }


def create_format_json_tool() -> Tool:
    return Tool(
        name="format_json",
        description="""Input is a raw text that may contain the following:
1. A portion or the entire content is in JSON format
2. Mixed with some explanatory text
3. Contains Markdown code blocks (```json or ```)
4. Contains <think> tags

Output is a pure JSON string without any other content.
Important: This tool only does formatting and does not modify the data itself. It ensures that the output is a valid JSON string.
Important: This tool's output is a string, not a JSON object. Pass it to the next tool without any processing.""",
        parameters={
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "The raw text to be formatted as JSON"
                }
            },
            "required": ["content"]
        }
    )


def create_search_knowledge_tool() -> Tool:
    return Tool(
        name="search_knowledge",
        description="""This tool searches for relevant knowledge from the knowledge base.
The knowledge base contains common knowledge about postgraduate entrance examination, including:
-公共课: politics, English, mathematics, etc.
-专业课: computer related, etc.

This tool can answer questions related to postgraduate entrance examination. 
If the question is not related to postgraduate entrance examination, please use search_internet tool instead.""",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query. Use keywords that are most relevant to the core of the problem, avoiding long sentences as much as possible."
                }
            },
            "required": ["query"]
        }
    )


def create_search_internet_tool() -> Tool:
    return Tool(
        name="search_internet",
        description="""This tool searches the internet for information.
Use this tool when:
1. The question is not related to postgraduate entrance examination
2. You need the latest information or data
3. You need to verify information from authoritative sources

For postgraduate entrance examination related questions, use search_knowledge tool instead.""",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query. Use keywords that are most relevant to the core of the problem, avoiding long sentences as much as possible."
                }
            },
            "required": ["query"]
        }
    )


def create_extract_questions_tool() -> Tool:
    return Tool(
        name="extract_questions",
        description="""This tool extracts question objects from the knowledge base.
Each question object has the following fields:
- question: str, the question text
- answer: str, the answer text
- question_type: str, the type of question, can be "single_choice", "multiple_choice", "true_false", "blank", "subjective", "unknown"
- options: Optional[List[str]], the options for choice questions, only for single_choice, multiple_choice, true_false
- analysis: Optional[str], the analysis of the answer
- knowledge_points: Optional[List[str]], the knowledge points related to the question

The output is a JSON array of question objects.
Important: This tool only extracts questions and does not do any other processing. The output should be a pure JSON array.""",
        parameters={
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "The raw text containing questions to be extracted"
                }
            },
            "required": ["content"]
        }
    )


def create_ocr_image_tool() -> Tool:
    return Tool(
        name="ocr_image",
        description="""This tool performs OCR (Optical Character Recognition) on an image to extract text.
It can handle:
- Screenshots
- Photos of documents
- Printed or handwritten text
- Charts and diagrams

The output is the extracted text from the image.""",
        parameters={
            "type": "object",
            "properties": {
                "image_url": {
                    "type": "string",
                    "description": "The URL or local path of the image to perform OCR on"
                }
            },
            "required": ["image_url"]
        }
    )


def create_save_note_tool() -> Tool:
    return Tool(
        name="save_note",
        description="""This tool saves a note to the knowledge base.
The note will be stored and can be retrieved later using the search_knowledge tool.
Use this tool to save important information or summaries that you want to remember.""",
        parameters={
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "The title of the note"
                },
                "content": {
                    "type": "string",
                    "description": "The content of the note"
                },
                "category": {
                    "type": "string",
                    "description": "The category of the note, e.g., 'math', 'English', 'politics', 'computer', 'other'"
                }
            },
            "required": ["title", "content", "category"]
        }
    )


def create_get_alerts_tool() -> Tool:
    return Tool(
        name="get_alerts",
        description="""This tool retrieves all alerts from the database.
An alert is a reminder for the user to review a specific question or knowledge point.
Each alert has the following fields:
- id: int, the unique identifier of the alert
- question_id: str, the unique identifier of the question
- question: str, the question text
- answer: str, the answer text
- question_type: str, the type of question
- options: Optional[List[str]], the options for choice questions
- analysis: Optional[str], the analysis of the answer
- knowledge_points: Optional[List[str]], the knowledge points related to the question
- next_review_time: str, the next time to review this question
- interval: int, the current interval in days

The output is a JSON array of alert objects.""",
        parameters={
            "type": "object",
            "properties": {},
            "required": []
        }
    )


def create_delete_alert_tool() -> Tool:
    return Tool(
        name="delete_alert",
        description="""This tool deletes an alert from the database.
The alert will be removed and will not appear in the alerts list anymore.""",
        parameters={
            "type": "object",
            "properties": {
                "alert_id": {
                    "type": "string",
                    "description": "The unique identifier of the alert to delete"
                }
            },
            "required": ["alert_id"]
        }
    )


def create_get_review_questions_tool() -> Tool:
    return Tool(
        name="get_review_questions",
        description="""This tool retrieves questions for review from the database.
It returns questions that are due for review based on the user's review history.
The questions are sorted by urgency (overdue questions first).

Each question has the following fields:
- id: str, the unique identifier of the question
- question: str, the question text
- answer: str, the answer text
- question_type: str, the type of question
- options: Optional[List[str]], the options for choice questions
- analysis: Optional[str], the analysis of the answer
- knowledge_points: Optional[List[str]], the knowledge points related to the question

The output is a JSON array of question objects.""",
        parameters={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "The maximum number of questions to retrieve. Default is 10."
                }
            },
            "required": []
        }
    )


def create_save_question_tool() -> Tool:
    return Tool(
        name="save_question",
        description="""This tool saves a question to the database.
The question will be stored and can be retrieved later using the get_review_questions tool.
If the question already exists (same question text), it will be updated.
Each question has the following fields:
- question: str, the question text (required)
- answer: str, the answer text (required)
- question_type: str, the type of question, can be "single_choice", "multiple_choice", "true_false", "blank", "subjective", "unknown" (required)
- options: Optional[List[str]], the options for choice questions
- analysis: Optional[str], the analysis of the answer
- knowledge_points: Optional[List[str]], the knowledge points related to the question

The output is the saved question object.""",
        parameters={
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The question text"
                },
                "answer": {
                    "type": "string",
                    "description": "The answer text"
                },
                "question_type": {
                    "type": "string",
                    "description": "The type of question"
                },
                "options": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "The options for choice questions"
                },
                "analysis": {
                    "type": "string",
                    "description": "The analysis of the answer"
                },
                "knowledge_points": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "The knowledge points related to the question"
                }
            },
            "required": ["question", "answer", "question_type"]
        }
    )


def create_get_question_history_tool() -> Tool:
    return Tool(
        name="get_question_history",
        description="""This tool retrieves the user's question practice history from the database.
It returns the history of questions that the user has practiced.
Each history entry has the following fields:
- id: str, the unique identifier of the history entry
- question_id: str, the unique identifier of the question
- question: str, the question text
- answer: str, the answer text
- user_answer: str, the user's answer
- is_correct: bool, whether the user's answer is correct
- question_type: str, the type of question
- options: Optional[List[str]], the options for choice questions
- analysis: Optional[str], the analysis of the answer
- knowledge_points: Optional[List[str]], the knowledge points related to the question
- timestamp: str, the time when the question was answered

The output is a JSON array of history objects.""",
        parameters={
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "The maximum number of history entries to retrieve. Default is 20."
                }
            },
            "required": []
        }
    )


def create_answer_question_tool() -> Tool:
    return Tool(
        name="answer_question",
        description="""This tool submits an answer for a question and records the result in the history.
The system will automatically check if the answer is correct and update the review schedule accordingly.
For choice questions, the answer should be the option letter (e.g., "A", "B", "C", "D").
For true/false questions, the answer should be "true" or "false".
For blank questions, the answer should be the exact blank content.
For subjective questions, the answer should be the text of the answer.""",
        parameters={
            "type": "object",
            "properties": {
                "question_id": {
                    "type": "string",
                    "description": "The unique identifier of the question"
                },
                "user_answer": {
                    "type": "string",
                    "description": "The user's answer to the question"
                }
            },
            "required": ["question_id", "user_answer"]
        }
    )


def create_add_review_tool() -> Tool:
    return Tool(
        name="add_review",
        description="""This tool adds a question to the review list.
The question will be added to the alerts and will be reviewed at the specified interval.
If the question already exists in the review list, it will update the review interval.
If question_id is not provided, the question will be searched by question text and the first match will be used.""",
        parameters={
            "type": "object",
            "properties": {
                "question_id": {
                    "type": "string",
                    "description": "The unique identifier of the question"
                },
                "question": {
                    "type": "string",
                    "description": "The question text (used if question_id is not provided)"
                },
                "interval": {
                    "type": "integer",
                    "description": "The review interval in days. Default is 1."
                }
            },
            "required": []
        }
    )


TOOLS = [
    create_format_json_tool(),
    create_search_knowledge_tool(),
    create_search_internet_tool(),
    create_extract_questions_tool(),
    create_ocr_image_tool(),
    create_save_note_tool(),
    create_get_alerts_tool(),
    create_delete_alert_tool(),
    create_get_review_questions_tool(),
    create_save_question_tool(),
    create_get_question_history_tool(),
    create_answer_question_tool(),
    create_add_review_tool(),
]


def get_tools() -> List[Dict[str, Any]]:
    return [tool.to_dict() for tool in TOOLS]
