# Kaoyan Copilot 🎓

全流程考研备考 AI 助手，基于 Multi-Agent 架构，提供择校咨询、知识点辅导、复习规划及心态建设等服务。

## ✨ 核心功能

系统包含多个垂直领域的智能体（Agents）：

- **Tutor Agent (导师)**: 学科知识解答、题目讲解，利用 RAG 技术基于教材回答。
- **Consultant Agent (咨询师)**: 院校数据查询、报录比分析、择校建议。
- **Planner Agent (规划师)**: 个性化复习计划制定、进度管理。
- **Mentor Agent (学长/学姐)**: 心理疏导、备考经验分享、加油打气。
- **Radar Agent (雷达)**: 每日自动监测目标院校官网更新（如招生简章、复试名单）。

## 🛠️ 技术架构

- **后端**: Python, FastAPI, LangChain, LangGraph
- **前端**: Next.js (React), Tailwind CSS
- **向量数据库**: ChromaDB (本地部署)
- **大模型支持**: OpenAI GPT-4, DeepSeek 等 (通过 LangChain 适配)

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

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 API Key (OPENAI_API_KEY 或 LLM_API_KEY)
```

### 3. 前端设置

```bash
cd web

# 安装依赖
npm install
# 或者使用 yarn / pnpm
# yarn install
# pnpm install
```

### 4. 运行项目

#### 方式 A: 完整全栈模式 (推荐)

1. **启动后端 API 服务**:
   ```bash
   # 在项目根目录下
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

#### 方式 B: Streamlit 原型模式 (仅后端)

如果你只想快速测试 Agent 逻辑，可以使用 Streamlit 界面：
```bash
streamlit run main.py
```

## 📂 项目结构

```
kaoyan_copilot/
├── app/                  # 后端核心代码
│   ├── agents/           # 各个垂直领域 Agent 实现 (Tutor, Planner, etc.)
│   ├── core/             # 核心逻辑 (LangGraph 状态, RAG 引擎, 工具集)
│   └── graph.py          # Agent 编排图 (Orchestrator)
├── data/                 # 数据存储
│   ├── vector_store/     # ChromaDB 向量数据库文件
│   └── documents/        # 原始文档 (PDF等)
├── web/                  # Next.js 前端项目
│   ├── components/       # React 组件
│   └── hooks/            # 自定义 Hooks
├── main.py               # Streamlit 入口文件 (原型演示)
├── server.py             # FastAPI 后端入口 (生产/Web服务)
├── ingest.py             # 数据处理/导入脚本
└── requirements.txt      # Python 依赖
```

## 📝 开发指南

- **新增 Agent**: 在 `app/agents/` 下创建新的 Agent 类，并在 `app/graph.py` 中注册。
- **RAG 数据管理**: 
  - 将 PDF 文档放入 `data/documents/`。
  - 运行脚本导入数据:
    ```bash
    python ingest.py path/to/your/document.pdf
    ```
  - 或者通过 API `/upload` 接口上传。
- **定时任务**: `server.py` 中包含后台调度器，默认每天 08:00 运行 Radar Agent。
