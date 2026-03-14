import os
import uuid
import asyncio
import datetime
import random
import requests
from contextlib import asynccontextmanager
from typing import Any, List, Dict

import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from langserve import add_routes
import langserve.serialization
from pydantic import BaseModel
from langgraph.types import Send
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

from app.infrastructure.config import settings
from app.runtime.graph.graph import app as graph_app
from app.skills.rag.rag_engine import RAGEngine
from app.skills.ocr.ocr_engine import ocr_engine
from app.agents.radar_agent import check_school_updates
from app.agents.politics_agent import check_politics_news
from app.infrastructure.database import history_manager, alert_manager, question_manager, review_manager


def custom_default(obj):
    if isinstance(obj, BaseModel):
        return obj.model_dump()
    if isinstance(obj, Send):
        return {"node": obj.node, "arg": obj.arg}
    if isinstance(obj, Exception):
        return str(obj)
    raise TypeError(f"Type is not JSON serializable: {type(obj)}")


langserve.serialization.default = custom_default


async def scheduled_radar_checks():
    print("后台调度器已启动：Radar Agent 检查任务。")
    while True:
        radar_config = settings.radar
        if not radar_config.enabled:
            await asyncio.sleep(60)
            continue

        schedule_time_str = radar_config.schedule_time
        try:
            target_hour, target_minute = map(int, schedule_time_str.split(":"))
        except:
            target_hour, target_minute = 8, 0

        now = datetime.datetime.now()
        target_time = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)

        if now >= target_time:
            target_time += datetime.timedelta(days=1)

        wait_seconds = (target_time - now).total_seconds()

        if wait_seconds > 60:
            await asyncio.sleep(60)
            continue

        if wait_seconds > 0:
            await asyncio.sleep(wait_seconds)

        radar_config = settings.radar
        if not radar_config.enabled:
            continue

        try:
            print(f"--- [Scheduled Task] 开始 Radar 检查 ({datetime.datetime.now()}) ---")
            target_school = radar_config.target_school
            alert = check_school_updates(target_school)

            if alert.has_critical_update:
                print(f"!!! 发现关键更新 !!!\n{alert.message}")
            else:
                print(f"检查完成。未发现 {target_school} 的新更新。")

        except Exception as e:
            print(f"Radar 调度任务出错: {e}")

        await asyncio.sleep(60)


async def scheduled_politics_checks():
    print("后台调度器已启动：Politics Agent 检查任务。")
    while True:
        politics_config = settings.politics
        if not politics_config.enabled:
            await asyncio.sleep(60)
            continue

        schedule_time_str = politics_config.schedule_time
        try:
            target_hour, target_minute = map(int, schedule_time_str.split(":"))
        except:
            target_hour, target_minute = 8, 30

        now = datetime.datetime.now()
        target_time = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)

        if now >= target_time:
            target_time += datetime.timedelta(days=1)

        wait_seconds = (target_time - now).total_seconds()

        if wait_seconds > 60:
            await asyncio.sleep(60)
            continue

        if wait_seconds > 0:
            await asyncio.sleep(wait_seconds)

        politics_config = settings.politics
        if not politics_config.enabled:
            continue

        try:
            print(f"--- [Scheduled Task] 开始 Politics 检查 ({datetime.datetime.now()}) ---")
            alert = check_politics_news()

            if alert.has_relevant_news and alert.news_items:
                print(f"!!! 发现 {len(alert.news_items)} 条重要考研时政 !!!")
                for item in alert.news_items:
                    print("-" * 30)
                    print(f"标题: {item.title}")
                    print(f"来龙去脉: {item.summary}")
                    print(f"考点: {item.exam_point}")
                    if item.source_url:
                        print(f"来源: {item.source_url}")
                print("-" * 30)
            else:
                print("检查完成。今日无重要考研时政。")

        except Exception as e:
            print(f"Politics 调度任务出错: {e}")

        await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(scheduled_radar_checks())
    asyncio.create_task(scheduled_politics_checks())
    yield


app = FastAPI(
    title="Kaoyan Copilot API",
    version="1.0",
    description="Kaoyan Copilot Agent 系统的后端 API",
    lifespan=lifespan,
)

server_config = settings.server
storage_config = settings.storage_local

app.add_middleware(
    CORSMiddleware,
    allow_origins=server_config.cors_origins,
    allow_credentials=server_config.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

documents_dir = storage_config.documents_dir
uploads_dir = storage_config.uploads_dir

os.makedirs(documents_dir, exist_ok=True)
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/files", StaticFiles(directory=documents_dir), name="files")
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

add_routes(
    app,
    graph_app,
    path="/chat",
    enable_feedback_endpoint=True,
)


@app.post("/upload")
async def upload_documents(files: List[UploadFile] = File(...)):
    upload_dir = storage_config.documents_dir
    os.makedirs(upload_dir, exist_ok=True)
    rag = RAGEngine()

    results = []
    success_count = 0

    for file in files:
        if not file.filename.endswith('.pdf'):
            results.append({"filename": file.filename, "status": "skipped", "message": "仅支持 PDF"})
            continue

        try:
            file_path = os.path.join(upload_dir, file.filename)

            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)

            success = rag.add_knowledge_base(file_path)

            if success:
                success_count += 1
                results.append({"filename": file.filename, "status": "success"})
            else:
                results.append({"filename": file.filename, "status": "failed", "message": "索引失败"})

        except Exception as e:
            results.append({"filename": file.filename, "status": "error", "message": str(e)})

    return {
        "message": f"处理完成: 成功 {success_count}/{len(files)}",
        "results": results,
        "count": success_count
    }


@app.post("/upload/image")
async def upload_image_and_ocr(file: UploadFile = File(...)):
    allowed_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp', '.pdf'}
    ext = os.path.splitext(file.filename)[1].lower()

    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {ext}")

    uploads_dir = storage_config.uploads_dir
    os.makedirs(uploads_dir, exist_ok=True)

    filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(uploads_dir, filename)

    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        print(f"正在处理 OCR 图片: {file_path}")
        extracted_text = ocr_engine.process_file(file_path)

        image_url = f"http://localhost:8000/uploads/{filename}"

        return {
            "filename": filename,
            "text": extracted_text,
            "url": image_url
        }

    except Exception as e:
        print(f"图片处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"图片处理失败: {str(e)}")


@app.get("/settings")
async def get_settings():
    return {
        "radar": {
            "enabled": settings.radar.enabled,
            "schedule_time": settings.radar.schedule_time,
            "target_school": settings.radar.target_school,
        },
        "politics": {
            "enabled": settings.politics.enabled,
            "schedule_time": settings.politics.schedule_time,
        },
        "general": {
            "exam_date": settings.general.exam_date,
        },
        "feature_flags": {
            "enable_docs_rag": settings.feature_flags.enable_docs_rag,
            "enable_chat_memory": settings.feature_flags.enable_chat_memory,
            "enable_self_correction": settings.feature_flags.enable_self_correction,
            "enable_human_approval": settings.feature_flags.enable_human_approval,
        },
    }


@app.post("/settings")
async def update_settings(new_config: Dict[str, Any]):
    if "radar" in new_config:
        radar_cfg = new_config["radar"]
        if "enabled" in radar_cfg:
            settings.radar.enabled = radar_cfg["enabled"]
        if "schedule_time" in radar_cfg:
            settings.radar.schedule_time = radar_cfg["schedule_time"]
        if "target_school" in radar_cfg:
            settings.radar.target_school = radar_cfg["target_school"]

    if "politics" in new_config:
        politics_cfg = new_config["politics"]
        if "enabled" in politics_cfg:
            settings.politics.enabled = politics_cfg["enabled"]
        if "schedule_time" in politics_cfg:
            settings.politics.schedule_time = politics_cfg["schedule_time"]

    if "general" in new_config:
        general_cfg = new_config["general"]
        if "exam_date" in general_cfg:
            settings.general.exam_date = general_cfg["exam_date"]

    return {"message": "Configuration updated", "config": await get_settings()}


@app.get("/quote")
async def get_quote():
    try:
        api_url = "https://api.t1qq.com/api/tool/daytry"
        params = {
            "key": "4jilHeggiK06Ir3QfWcepojJYg",
            "time": "random"
        }

        resp = requests.get(api_url, params=params, timeout=5)

        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 200:
                quote_data = data.get("data", {})
                note = quote_data.get("note")

                if note:
                    return {"quote": note}
    except Exception as e:
        print(f"Quote API fetch failed: {e}")
        pass

    quotes = [
        "星光不问赶路人，时光不负有心人。",
        "既然选择了远方，便只顾风雨兼程。",
        "种一棵树最好的时间是十年前，其次是现在。",
        "研途漫漫，终抵彼岸。",
        "关关难过关关过，前路漫漫亦灿灿。",
        "看似不起眼的日复一日，会在将来的某一天，突然让你看到坚持的意义。",
        "往事暗沉不可追，来日之路光明灿烂。",
        "你的负担将变成礼物，你受的苦将照亮你的路。",
        "须知少时凌云志，曾许人间第一流。",
        "乾坤未定，你我皆是黑马。"
    ]
    return {"quote": random.choice(quotes)}


@app.get("/alerts")
async def get_alerts():
    return alert_manager.get_alerts()


@app.post("/radar/check")
async def force_radar_check():
    try:
        target_school = settings.radar.target_school

        alert = check_school_updates(target_school)

        result = alert_manager.update_radar(
            school_name=target_school,
            has_update=alert.has_critical_update,
            message=alert.message,
            url=alert.source_url
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/politics/check")
async def force_politics_check():
    try:
        alert = check_politics_news()

        news_items = [item.model_dump() for item in alert.news_items] if alert.news_items else []

        result = alert_manager.update_politics(
            has_news=alert.has_relevant_news,
            news_items=news_items
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history/{user_id}")
async def get_history(user_id: str):
    history = history_manager.get_history(user_id)
    return {"user_id": user_id, "history": history}


@app.post("/history/{user_id}/save")
async def save_history(user_id: str, payload: Dict[str, Any]):
    try:
        session_id = payload.get("session_id")
        messages = payload.get("messages")
        title = payload.get("title")

        if not session_id or messages is None:
            raise HTTPException(status_code=400, detail="Missing session_id or messages")

        session = history_manager.save_session(
            user_id=user_id,
            session_id=session_id,
            messages=messages,
            title=title
        )
        return {"message": "Saved successfully", "session": session}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/history/{user_id}/{session_id}")
async def delete_history_session(user_id: str, session_id: str):
    success = history_manager.delete_session(user_id, session_id)
    if success:
        return {"message": "Session deleted"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")


@app.get("/api/questions")
async def get_questions(subject: str = None, year: int = None, limit: int = 10, offset: int = 0):
    return question_manager.get_questions(subject, year, limit, offset)


@app.get("/api/questions/{id}")
async def get_question(id: int):
    q = question_manager.get_question_by_id(id)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    return q


@app.post("/api/questions/submit")
async def submit_answer(payload: Dict[str, Any]):
    user_id = payload.get("user_id", "default_user")
    question_id = payload.get("question_id")
    selected_option = payload.get("selected_option")

    if not question_id or not selected_option:
        raise HTTPException(status_code=400, detail="Missing question_id or selected_option")

    try:
        result = question_manager.submit_answer(user_id, question_id, selected_option)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/questions/{id}/variations")
async def get_variations(id: int):
    return question_manager.get_similar_questions(id)


@app.get("/api/error-book")
async def get_error_book():
    return review_manager.get_due_reviews()


@app.post("/api/error-book/review")
async def submit_review(payload: Dict[str, Any]):
    task_id = payload.get("task_id")
    quality = payload.get("quality")

    if task_id is None or quality is None:
        raise HTTPException(status_code=400, detail="Missing task_id or quality")

    result = review_manager.submit_review_feedback(task_id, quality)
    return {"message": result}


@app.get("/api/stats/radar")
async def get_radar_stats(user_id: str = "default_user"):
    return question_manager.get_radar_stats(user_id)


if __name__ == "__main__":
    uvicorn.run(app, host=server_config.host, port=server_config.port)
