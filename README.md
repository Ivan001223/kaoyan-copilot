# Kaoyan Copilot 🎓

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688?style=flat&logo=fastapi&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-Latest-FF6F61?style=flat&logo=langchain&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-14-000000?style=flat&logo=next.js&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg)

**全流程考研备考 AI 助手** · 基于 Multi-Agent + LangGraph 架构

[核心功能](#-核心功能) · [技术架构](#-技术架构) · [快速开始](#-快速开始) · [项目结构](#-项目结构)

</div>

---

## ✨ 核心功能

> 8 大智能体协同工作，打造全方位考研备考体验

| Agent | 角色 | 功能描述 |
|:---:|:---:|:---|
| 🎓 | **Tutor Agent** | 学科知识解答、题目讲解，苏格拉底式教学引导 |
| 📊 | **Consultant Agent** | 院校数据查询、报录比分析、智能择校建议 |
| 📅 | **Planner Agent** | 个性化复习计划制定、进度追踪管理 |
| 🎯 | **Estimator Agent** | 科学估分、上岸概率分析、生成诊断报告 |
| 🎭 | **Interviewer Agent** | 模拟复试场景，专业提问与点评 |
| 📰 | **Politics Agent** | 每日时政筛选，提取背诵考点 |
| 💪 | **Mentor Agent** | 心理疏导、经验分享、加油打气 |
| 🔭 | **Radar Agent** | 目标院校官网监控，实时推送通知 |

### 🧠 核心能力

- **多模态 RAG**: 基于 Qwen-VL-Embedding，实现图文混合检索
- **OCR 文字识别**: 支持 PDF、数学公式高精度提取
- **智能路由**: LangGraph Supervisor 架构自动分配任务

---

## 🛠️ 技术架构

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Next.js)                     │
│                  Tailwind CSS · TypeScript                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI + LangServe                      │
│                   REST API · WebSocket                      │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    LangGraph Runtime                        │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│   │Orchestrtr│  │  State   │  │  Nodes   │  │ Routers  │  │
│   └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      Skills / Services                      │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐   │
│  │  RAG   │ │ Memory │ │   OCR   │ │Research│ │ Tools  │   │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   Infrastructure                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│  │ ChromaDB │ │   LLM    │ │ Config   │ │   Database    │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 🏗️ 技术栈

| 层级 | 技术 |
|:---|:---|
| **后端** | Python 3.11, FastAPI, LangChain, LangGraph |
| **前端** | Next.js 14, React, Tailwind CSS, TypeScript |
| **向量库** | ChromaDB / FAISS |
| **大模型** | Qwen / Kimi / DeepSeek / OpenAI |
| **OCR** | Qwen-VL, PyPDF, Unstructured |

---

## 🚀 快速开始

### 1. 环境要求

```bash
Python 3.10+  ·  Node.js 18+  ·  Git
```

### 2. 克隆项目

```bash
git clone https://github.com/Ivan001223/kaoyan-copilot.git
cd kaoyan-copilot
```

### 3. 安装依赖

```bash
# 创建虚拟环境
conda create -n kaoyan python=3.11 -y
conda activate kaoyan

# 安装 Python 依赖
pip install -r requirements.txt
```

### 4. 配置

```bash
# 复制配置模板
cp configs/config.json configs/config.json

# 编辑配置文件，填入你的 API Keys
vim configs/config.json
```

**config.json 示例:**
```json
{
  "llm": {
    "api_key": "your-api-key",
    "base_url": "https://api.moonshot.cn/v1",
    "model": "kimi-k2-turbo-preview"
  },
  "embeddings": {
    "provider": "modelscope",
    "model_name": "AI-ModelScope/bge-large-zh-v1.5"
  }
}
```

### 5. 启动服务

```bash
# 启动后端 (AgFrame 架构)
python -m app.server.main
# 或
cd app && uvicorn server.main:app --reload --port 8000

# 启动前端 (新终端)
cd web && npm run dev
```

**访问地址:**
- 🌐 前端: http://localhost:3000
- 📚 API Docs: http://localhost:8000/docs
- 💬 Chat: http://localhost:8000/chat

---

## 📂 项目结构

```
kaoyan-copilot/
├── app/                           # 🆕 AgFrame 架构
│   ├── agents/                    # 8 大 Agent 节点
│   │   ├── tutor_agent.py        # 导师 Agent
│   │   ├── consultant_agent.py   # 择校 Agent
│   │   ├── planner_agent.py      # 规划 Agent
│   │   ├── estimator_agent.py    # 估分 Agent
│   │   ├── interviewer_agent.py  # 面试 Agent
│   │   ├── politics_agent.py     # 时政 Agent
│   │   ├── mentor_agent.py       # 心态 Agent
│   │   └── radar_agent.py       # 院校监控 Agent
│   │
│   ├── infrastructure/            # 基础设施层
│   │   ├── config/               # 配置管理 (Pydantic Settings)
│   │   ├── database/             # 数据库 (MySQL + Managers)
│   │   └── utils/                # 工具函数
│   │
│   ├── runtime/                   # 运行时核心
│   │   ├── graph/                # LangGraph 工作流
│   │   │   ├── state.py          # State 定义
│   │   │   ├── graph.py          # 图编排
│   │   │   └── orchestrator.py   # 路由决策
│   │   └── llm/                  # LLM 工厂
│   │
│   ├── server/                    # FastAPI 服务
│   │   └── main.py               # 服务入口
│   │
│   └── skills/                    # 技能模块
│       ├── rag/                   # RAG 检索
│       ├── ocr/                   # 文字识别
│       └── common/                 # 公共工具
│
├── backend/                        # 旧架构 (已废弃)
│   └── data/                      # 数据文件保留
│
├── configs/                        # 配置文件
│   └── config.json
│
├── web/                           # Next.js 前端
│   ├── app/                       # 页面组件
│   ├── components/                # UI 组件
│   └── services/                  # API 调用
│
└── requirements.txt                # Python 依赖
```

---

## 📝 开发指南

### 🆕 添加新 Agent

1. 在 `app/agents/` 创建 Agent 文件
2. 实现 `get_xxx_node()` 函数返回 LangGraph 节点
3. 在 `app/runtime/graph/graph.py` 注册节点

```python
# app/agents/my_agent.py
def get_my_node():
    def my_node(state: AgentState):
        # Agent 逻辑
        return {"messages": [...]}
    return my_node
```

### 📚 RAG 数据管理

```bash
# 上传 PDF 文档
curl -X POST http://localhost:8000/upload \
  -F "files=@document.pdf"
```

### ⚙️ 模型配置

在 `configs/config.json` 中修改:

```json
{
  "llm": {
    "model": "qwen-turbo",
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"
  },
  "embeddings": {
    "model_name": "bge-large-zh-v1.5"
  }
}
```

---

## 📄 License

Apache-2.0 License · © 2026 Kaoyan Copilot

---

<div align="center">

**Made with ❤️ for考研ers**

</div>
