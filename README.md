# Kaoyan Copilot 🎓

全流程考研备考 AI 助手，基于 Multi-Agent 架构，提供择校咨询、知识点辅导、复习规划、模拟复试及心态建设等服务。

## ✨ 核心功能

系统包含多个垂直领域的智能体（Agents）及核心能力：

- **Tutor Agent (导师)**: 学科知识解答、题目讲解，利用 RAG 技术基于教材回答。
- **Consultant Agent (咨询师)**: 院校数据查询、报录比分析、择校建议。
- **Planner Agent (规划师)**: 个性化复习计划制定、进度管理。
- **Estimator Agent (估分师)**: 基于模拟成绩、目标院校分数线及学习习惯，科学估算上岸概率并生成分析报告。
- **Interviewer Agent (面试官)**: 模拟研究生复试场景（"张教授"），进行专业提问，并对回答的逻辑、词汇及自信度进行打分点评。
- **Politics Agent (时政专员)**: 每日自动检索并筛选考研政治相关的时政新闻（如重要会议、讲话），提取背诵考点。
- **Mentor Agent (学长/学姐)**: 心理疏导、备考经验分享、加油打气。
- **Radar Agent (雷达)**: 每日自动监测目标院校官网更新（如招生简章、复试名单）。

### 🧠 核心能力
- **OCR & 公式识别**: 集成 DeepSeek-OCR / Qwen-VL，支持高精度识别数学公式、PDF文档并转换为 Markdown 格式，方便知识库构建。
- **多模态 RAG**: 支持图文混合检索，基于 Qwen-VL-Embedding 实现。

## 🛠️ 技术架构

- **后端**: Python 3.11, FastAPI, LangChain, LangGraph
- **前端**: Next.js 14 (React), Tailwind CSS, TypeScript
- **向量数据库**: ChromaDB (本地持久化)
- **大模型支持**: Qwen (本地/API), DeepSeek, OpenAI
- **OCR/多模态**: DeepSeek-OCR, Qwen-VL-Utils
- **工具集**: DuckDuckGo Search (时政搜索), PyPDF

## 🚀 快速开始

### 1. 环境准备

确保你的系统已安装：
- Python 3.10+
- Node.js 18+ (用于 Web 前端)
- Conda (推荐)

### 2. 后端设置

```bash
# 1. 创建并激活 Conda 环境
conda create -n kaoyan_copilot python=3.11 -y
conda activate kaoyan_copilot

# 2. 进入后端目录
cd backend

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp config.example.json config.json
# 编辑 config.json 填入你的 API Keys (如 DeepSeek API, OpenAI API 等)
```

### 3. 前端设置

```bash
# 回到项目根目录
cd ../web

# 安装依赖
npm install
# 或者使用 yarn / pnpm
# yarn install
# pnpm install
```

### 4. 运行项目

1. **启动后端 API 服务**:
   ```bash
   # 在 backend 目录下
   python server.py
   ```
   - 后端服务将运行在: `http://localhost:8000`
   - API 文档 (Swagger UI): `http://localhost:8000/docs`

2. **启动 Web 前端**:
   ```bash
   # 新开一个终端窗口，进入 web 目录
   cd web
   npm run dev
   ```
   - 访问前端页面: `http://localhost:3000`

## 📂 项目结构

```
kaoyan_copilot/
├── backend/                  # 后端项目目录
│   ├── app/                  # 后端核心代码
│   │   ├── agents/           # 各个垂直领域 Agent 实现
│   │   ├── core/             # 核心逻辑
│   │   │   ├── workflow/     # LangGraph 编排 (graph.py)
│   │   │   ├── database/     # 数据库交互
│   │   │   └── llm/          # 模型加载与 Embeddings
│   │   └── server.py         # FastAPI 后端入口
│   ├── data/                 # 数据存储
│   │   ├── vector_store/     # ChromaDB 向量库文件
│   │   └── documents/        # 原始 PDF 文档
│   ├── scripts/              # 工具脚本 (ingest.py, seed_mysql.py)
│   └── requirements.txt      # Python 依赖
├── web/                      # Next.js 前端项目
│   ├── app/                  # Next.js App Router 页面
│   ├── components/           # React 组件
│   └── services/             # API 请求封装
└── README.md                 # 项目说明
```

## 📝 开发指南

- **新增 Agent**: 在 `backend/app/agents/` 下创建新的 Agent 类，并在 `backend/app/core/workflow/graph.py` 中注册。
- **RAG 数据管理**: 
  - 将 PDF 文档放入 `backend/data/documents/`。
  - 运行脚本导入数据 (支持 OCR):
    ```bash
    # 在 backend 目录下
    python scripts/ingest.py
    ```
  - 或者通过前端/API 上传接口进行文档处理。
- **模型配置**: 在 `backend/config.json` 中修改模型路径或 API Key。
