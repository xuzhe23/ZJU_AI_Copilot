# 求是·研伴 ZJU ResearchMate

> 浙江大学校园 AI 创新应用大赛（2026 · 智创校园·浙晓未来）参赛项目
> 选题方向：**科研创新** —— 科研日常 routine 自动化 + 经验知识库问答 + 训练数据一键整理

一个「本地优先、平台可插拔」的科研 AI 管家：把研究生每天重复的「盯数据、搭报表、问常识」交给它，
让师兄师姐的踩坑经验从「人走经验丢」变成「越用越值钱的私有知识资产」。

---

## 一、三条命令讲清价值（演示核心）

| 命令 | 解决什么 | 对应比赛叙事 |
|---|---|---|
| `python main.py report` | 自动汇总当日采集记录，生成科研日报 | routine 自动化 |
| `python main.py ask "实验室GPU环境怎么配置"` | 知识库问答，带引用来源 | 经验资产化 / AI 解答工具人 |
| `python main.py feed` | 一键导出脱敏后的标准训练集 JSONL | 自动 feed（用日常记录训练 AI） |

## 二、快速开始（零依赖，离线可跑）

```bash
# 环境：D:\anaconda3\envs\yolov8（Python 3.10.20）
cd /d/课件和作业/作业和文档/大四上/AI竞赛

# 方式 A：一键离线演示（推荐，录屏就用它）
"D:/anaconda3/envs/yolov8/python.exe" main.py demo

# 方式 B：逐步执行
"D:/anaconda3/envs/yolov8/python.exe" main.py ingest          # 1. 建知识库
"D:/anaconda3/envs/yolov8/python.exe" main.py collect         # 2. 日常采集
"D:/anaconda3/envs/yolov8/python.exe" main.py report          # 3. 生成日报
"D:/anaconda3/envs/yolov8/python.exe" main.py ask "显存不足怎么办"   # 4. 问答
"D:/anaconda3/envs/yolov8/python.exe" main.py feed            # 5. 导出训练集

# 图片 OCR（把任意图片转文字）
"D:/anaconda3/envs/yolov8/python.exe" main.py ocr path/to/image.jpg
```

## 三、启用平台 API（可选）

复制 `.env.example` 为 `.env`，填入 Key，把 `OFFLINE_MODE` 改为 `false`：

```ini
OFFLINE_MODE=false
DASHSCOPE_API_KEY=sk-xxxxxxxx        # 千问/百炼：数据处理 + 对话输出
ZJU_API_KEY=                         # 浙大教育智能体平台：数据来源（OpenAI 兼容）
```

平台分工（含对「Qoder=对话输出」的修正）：

| 角色 | 平台 | 接入 |
|---|---|---|
| 数据来源 | 浙大教育智能体平台 `aihub.zju.edu.cn`（Dify 构建） | OpenAI 兼容 `/chat/completions` |
| 数据处理 | 千问办公 → DashScope（Qwen3.8） | `dashscope.aliyuncs.com/compatible-mode/v1` + embedding/rerank |
| 对话输出 | 千问 DashScope（Qoder 是编程 Agent 平台，官方无 chat 接口，故改用它） | 同上 |

> **核心工程原则**：三平台全部是可插拔 Provider，拿不到 Key 时自动降级到本地零依赖实现，
> 核心闭环离线即可完整演示，不把项目生死押在某个平台接口上。

## 四、目录结构

```
AI竞赛/
├── main.py                   # CLI 入口
├── .env.example              # 配置模板
├── requirements.txt          # 依赖清单
├── 方案与大纲.md             # 完整方案文档（比赛叙事/架构/评审要点）
├── config/settings.py        # 配置中心（读 .env，集中管理 Key/模型/路径）
├── core/                     # 数据模型 + Provider 抽象接口
├── collectors/               # 定时调度 / 目录监控 / 网页抓取
├── ocr/ocr_engine.py         # 图片 OCR（RapidOCR）
├── parsers/doc_parser.py     # 文档解析 + 分块
├── knowledge/                # 本地 TF-IDF 索引 + 持久化
├── retrieval/retriever.py    # 检索 + 可选重排
├── llm/                      # 平台 Provider + 本地兜底
├── report/reporter.py        # 日报生成
├── qa/answerer.py            # 知识库问答
├── datasets/feed_builder.py  # 训练集导出 + 脱敏
├── web/app.py                # 可选 Gradio 网页
└── data/                     # ingest 输入 / kb 索引 / logs 记录 / outputs 输出
```

## 五、比赛提交清单（对应官方要求）

1. **申报书** — 见 `方案与大纲.md` 的「叙事八要素」，可直接改写；
2. **原创承诺书** — 负责人签字扫描件；
3. **作品介绍文档** — 作品名称、3~5 个关键词、作品概要、核心痛点、落地场景、预期成效；
4. **演示视频** ≤10 分钟、≤200MB —— 建议：作品概述 ≤2min + `demo` 实操 ≤6min + 成效反思 ≤2min；
5. **支撑材料** —— 本代码库 + `data/outputs` 生成的日报/训练集产物。

> ⏰ 时间提醒：报名 **10-18** 截止、作品提交 **10-21** 截止，请以「跑通 demo + 录屏」为第一优先级。
