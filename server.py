import os
import uvicorn
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from langserve import add_routes
from pydantic import BaseModel
from typing import List, Dict, Any
import langserve.serialization
from langgraph.types import Send

# --- PATCH: Fix langserve serialization for Send objects and broken default ---
def custom_default(obj):
    if isinstance(obj, BaseModel):
        return obj.model_dump()
    if isinstance(obj, Send):
        return {"node": obj.node, "arg": obj.arg}
    if isinstance(obj, Exception):
        return str(obj)
    # For other types, we must raise TypeError so orjson can handle it (or fail gracefully)
    # The original implementation called super().default(obj) which crashed.
    raise TypeError(f"Type is not JSON serializable: {type(obj)}")

langserve.serialization.default = custom_default
# -----------------------------------------------------------------------------

from app.core.graph import app as graph_app
from app.core.rag_engine import RAGEngine
from app.core.config_manager import config_manager
from app.core.model_loader import check_and_download_models

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 检查并下载本地模型
    check_and_download_models()
    
    # 启动后台任务
    # Note: scheduled_radar_checks and scheduled_politics_checks are defined later in this file.
    # Python allows this forward reference as long as they are defined when lifespan is executed (at startup).
    asyncio.create_task(scheduled_radar_checks())
    asyncio.create_task(scheduled_politics_checks())
    yield

# 1. 初始化 FastAPI
app = FastAPI(
    title="Kaoyan Copilot API",
    version="1.0",
    description="Kaoyan Copilot Agent 系统的后端 API",
    lifespan=lifespan
)

# 2. CORS 设置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 仅供开发使用，生产环境请使用特定来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. LangServe 路由
# 将 LangGraph 应用程序公开为可调用对象
# 路径：/chat
add_routes(
    app,
    graph_app,
    path="/chat",
    enable_feedback_endpoint=True,
)

# 3.1 静态文件服务 (用于访问上传的文档)
os.makedirs(os.path.join("data", "documents"), exist_ok=True)
app.mount("/files", StaticFiles(directory=os.path.join("data", "documents")), name="files")

# 3.2 静态文件服务 (用于访问上传的图片)
os.makedirs(os.path.join("data", "uploads"), exist_ok=True)
app.mount("/uploads", StaticFiles(directory=os.path.join("data", "uploads")), name="uploads")

# 4. RAG 上传端点
@app.post("/upload")
async def upload_documents(files: List[UploadFile] = File(...)):
    """
    上传多个 PDF 文件，保存并将其摄取到 RAG 向量存储中。
    """
    upload_dir = os.path.join("data", "documents")
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
                
            # 触发摄取
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

# 4.1 OCR 上传端点 (新增)
from app.core.ocr_engine import ocr_engine

@app.post("/upload/image")
async def upload_image_and_ocr(file: UploadFile = File(...)):
    """
    上传图片，保存并返回图片的 URL (以及 OCR 文本作为备用)。
    """
    # 允许的图片扩展名
    allowed_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp', '.pdf'}
    ext = os.path.splitext(file.filename)[1].lower()
    
    if ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {ext}")

    # Ensure uploads directory exists
    uploads_dir = os.path.join("data", "uploads")
    os.makedirs(uploads_dir, exist_ok=True)
    
    # Generate unique filename
    import uuid
    filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(uploads_dir, filename)
    
    # Save file persistently
    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
            
        # Call OCR engine for text extraction (as a fallback/supplement)
        print(f"正在处理 OCR 图片: {file_path}")
        extracted_text = ocr_engine.process_file(file_path)
        
        # Return URL for the frontend to use in multimodal messages
        # Assuming app is mounted at root and "uploads" static mount (we need to add this mount)
        image_url = f"http://localhost:8000/uploads/{filename}"
        
        return {
            "filename": filename, 
            "text": extracted_text,
            "url": image_url
        }
        
    except Exception as e:
        print(f"图片处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"图片处理失败: {str(e)}")

# 4.2 设置端点
@app.get("/settings")
async def get_settings():
    """获取当前系统配置"""
    return config_manager.get_config()

@app.post("/settings")
async def update_settings(new_config: Dict[str, Any]):
    """更新系统配置"""
    updated_config = config_manager.update_config(new_config)
    return {"message": "Configuration updated", "config": updated_config}


# 4.5 后台调度器 (Radar Agent 自动检查)
import datetime
from app.agents.radar_agent import check_school_updates

async def scheduled_radar_checks():
    """
    根据配置运行 Radar Agent 检查。
    """
    print("后台调度器已启动：Radar Agent 检查任务。")
    while True:
        # 每次循环都重新读取配置，以便动态调整
        radar_config = config_manager.get_config().get("radar", {})
        if not radar_config.get("enabled", True):
            await asyncio.sleep(60)
            continue
            
        schedule_time_str = radar_config.get("schedule_time", "08:00")
        try:
            target_hour, target_minute = map(int, schedule_time_str.split(":"))
        except:
            target_hour, target_minute = 8, 0
            
        now = datetime.datetime.now()
        target_time = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
        
        if now >= target_time:
            # 如果今天已经过了目标时间，安排在明天
            target_time += datetime.timedelta(days=1)
            
        wait_seconds = (target_time - now).total_seconds()
        # 如果等待时间太长（比如通过配置修改了时间，导致需要等待很久），
        # 我们每隔一段时间（例如 60s）醒来一次检查配置变更
        
        if wait_seconds > 60:
             await asyncio.sleep(60)
             continue 

        # 接近目标时间，进行精确等待
        if wait_seconds > 0:
             await asyncio.sleep(wait_seconds)
        
        # 再次检查配置，确保未被禁用
        radar_config = config_manager.get_config().get("radar", {})
        if not radar_config.get("enabled", True):
            continue

        # 执行检查
        try:
            print(f"--- [Scheduled Task] 开始 Radar 检查 ({datetime.datetime.now()}) ---")
            default_school = radar_config.get("target_school", "中国科学院大学杭州高等研究所")
            alert = check_school_updates(default_school)
            
            if alert.has_critical_update:
                print(f"!!! 发现关键更新 !!!\n{alert.message}")
                # TODO: 这里可以集成推送通知（例如邮件、WebSocket 推送到前端）
            else:
                print(f"检查完成。未发现 {default_school} 的新更新。")
                
        except Exception as e:
            print(f"Radar 调度任务出错: {e}")
            
        # 避免快速循环，稍微等待一下以越过目标时间
        await asyncio.sleep(60)

# 4.6 后台调度器 (Politics Agent 自动检查)
from app.agents.politics_agent import check_politics_news

async def scheduled_politics_checks():
    """
    根据配置运行 Politics Agent 检查。
    """
    print("后台调度器已启动：Politics Agent 检查任务。")
    while True:
        politics_config = config_manager.get_config().get("politics", {})
        if not politics_config.get("enabled", True):
            await asyncio.sleep(60)
            continue

        schedule_time_str = politics_config.get("schedule_time", "08:30")
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
            
        politics_config = config_manager.get_config().get("politics", {})
        if not politics_config.get("enabled", True):
            continue

        # 执行检查
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
                # TODO: 集成推送通知
            else:
                print("检查完成。今日无重要考研时政。")
                
        except Exception as e:
            print(f"Politics 调度任务出错: {e}")
            
        await asyncio.sleep(60)

# 5. 历史记录端点
from app.core.history_manager import history_manager
from app.core.alert_manager import alert_manager
import requests
import random

@app.get("/quote")
async def get_quote():
    """Fetch a random inspirational quote"""
    try:
        # User requested API: https://api.t1qq.com/api/tool/daytry
        # Note: This API requires a key. Since we don't have one, this call is expected to fail (403/401).
        # We implement it as requested but provide a robust fallback to ensure the UI works.
        
        api_url = "https://api.t1qq.com/api/tool/daytry"
        # Using the key provided by the user
        params = {
            "key": "4jilHeggiK06Ir3QfWcepojJYg", 
            "time": "random"
        }
        
        # Use a short timeout to fail fast if the API is slow/unresponsive
        resp = requests.get(api_url, params=params, timeout=5) # Increased timeout slightly
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get("code") == 200:
                # API Response Structure:
                # {
                #   "code": 200,
                #   "msg": "查询成功",
                #   "data": {
                #       "tts": "...",
                #       "content": "Nothing like a little truth to sober you up.",
                #       "note": "唯有事实最能让人清醒。",
                #       ...
                #   }
                # }
                quote_data = data.get("data", {})
                note = quote_data.get("note")
                # content = quote_data.get("content") # English version, optional
                
                if note:
                    return {"quote": note}
    except Exception as e:
        print(f"Quote API fetch failed: {e}")
        pass

    # Fallback to local quotes if API fails
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
    """获取最新的监控警报状态"""
    return alert_manager.get_alerts()

@app.post("/radar/check")
async def force_radar_check():
    """强制执行院校监控检查"""
    try:
        radar_config = config_manager.get_config().get("radar", {})
        target_school = radar_config.get("target_school", "中国科学院大学杭州高等研究所")
        
        # 异步运行以避免阻塞（虽然这里为了返回结果我们同步调用）
        # 注意：Search 可能会花几秒钟
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
    """强制执行时政新闻检查"""
    try:
        alert = check_politics_news()
        
        # Convert Pydantic models to dicts
        news_items = [item.dict() for item in alert.news_items] if alert.news_items else []
        
        result = alert_manager.update_politics(
            has_news=alert.has_relevant_news,
            news_items=news_items
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history/{user_id}")
async def get_history(user_id: str):
    """
    检索用户的聊天记录列表。
    """
    history = history_manager.get_history(user_id)
    return {"user_id": user_id, "history": history}

@app.post("/history/{user_id}/save")
async def save_history(user_id: str, payload: Dict[str, Any]):
    """
    保存或更新聊天会话。
    """
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
    """
    删除特定的聊天会话。
    """
    success = history_manager.delete_session(user_id, session_id)
    if success:
        return {"message": "Session deleted"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")

if __name__ == "__main__":
    import uvicorn
    # 生产环境中运行：uvicorn server:app --host 0.0.0.0 --port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
