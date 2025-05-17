# 🧠 Greeum v0.5.0

<p align="center">
  <a href="../../README.md">🇰🇷 한국어</a> |
  <a href="README_EN.md">🇺🇸 English</a> |
  <a href="README_ZH.md">🇨🇳 中文</a> |
  <a href="README_JP.md">🇯🇵 日本語</a> |
  <a href="README_ES.md">🇪🇸 Español</a> |
  <a href="README_DE.md">🇩🇪 Deutsch</a> |
  <a href="README_FR.md">🇫🇷 Français</a>
</p>

多语言 LLM 独立记忆管理系统

## 📌 概述

Greeum 是基于 RAG（检索增强生成，Retrieval-Augmented Generation）架构的 LLM 独立记忆系统。它实现了 RAG 的核心组件，包括信息存储和检索（block_manager.py）、相关记忆管理（cache_manager.py）和提示增强（prompt_wrapper.py），以生成更准确、更符合上下文的响应。

**Greeum**（发音：gri-eum）是一个可以连接到任何 LLM（大型语言模型）的**通用记忆模块**，提供以下功能：
- 长期跟踪用户话语、目标、情绪和意图
- 回忆与当前上下文相关的记忆
- 在多语言环境中识别和处理时间表达式
- 作为"有记忆的 AI"运行

"Greeum"这个名字灵感来自韩语"그리움"（思念/回忆），完美地捕捉了记忆系统的本质。

## 🔑 主要功能

- **类区块链长期记忆 (LTM)**：具有不可变性的基于区块的记忆存储
- **基于 TTL 的短期记忆 (STM)**：高效管理临时重要信息
- **语义相关性**：基于关键词/标签/向量的记忆回忆系统
- **路点缓存**：自动检索与当前上下文相关的记忆
- **提示词合成器**：自动生成包含相关记忆的 LLM 提示词
- **时间推理器**：在多语言环境中的高级时间表达式识别
- **多语言支持**：自动检测和处理韩语、英语等语言
- **模型控制协议**：通过单独的 [GreeumMCP](https://github.com/DryRainEnt/GreeumMCP) 包支持 Cursor、Unity、Discord 等外部工具集成

## ⚙️ 安装

1. 克隆仓库
   ```bash
   git clone https://github.com/DryRainEnt/Greeum.git
   cd Greeum
   ```

2. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```

## 🧪 使用方法

### 命令行界面

```bash
# 添加长期记忆
python cli/memory_cli.py add -c "开始了一个新项目，真的很令人兴奋"

# 通过关键词搜索记忆
python cli/memory_cli.py search -k "项目,兴奋"

# 通过时间表达式搜索记忆
python cli/memory_cli.py search-time -q "我三天前做了什么？" -l "zh"

# 添加短期记忆
python cli/memory_cli.py stm "今天天气真好"

# 获取短期记忆
python cli/memory_cli.py get-stm

# 生成提示词
python cli/memory_cli.py prompt -i "项目进展如何？"
```

### REST API 服务器

```bash
# 运行 API 服务器
python api/memory_api.py
```

Web 界面：http://localhost:5000

API 端点：
- GET `/api/v1/health` - 健康检查
- GET `/api/v1/blocks` - 列出区块
- POST `/api/v1/blocks` - 添加区块
- GET `/api/v1/search?keywords=keyword1,keyword2` - 通过关键词搜索
- GET `/api/v1/search/time?query=yesterday&language=en` - 通过时间表达式搜索
- GET, POST, DELETE `/api/v1/stm` - 管理短期记忆
- POST `/api/v1/prompt` - 生成提示词
- GET `/api/v1/verify` - 验证区块链完整性

### Python 库

```python
from greeum import BlockManager, STMManager, CacheManager, PromptWrapper
from greeum.text_utils import process_user_input
from greeum.temporal_reasoner import TemporalReasoner

# 处理用户输入
user_input = "开始了一个新项目，真的很令人兴奋"
processed = process_user_input(user_input)

# 使用区块管理器存储记忆
block_manager = BlockManager()
block = block_manager.add_block(
    context=processed["context"],
    keywords=processed["keywords"],
    tags=processed["tags"],
    embedding=processed["embedding"],
    importance=processed["importance"]
)

# 基于时间的搜索（多语言）
temporal_reasoner = TemporalReasoner(db_manager=block_manager, default_language="auto")
time_query = "我三天前做了什么？"
time_results = temporal_reasoner.search_by_time_reference(time_query)

# 生成提示词
cache_manager = CacheManager(block_manager=block_manager)
prompt_wrapper = PromptWrapper(cache_manager=cache_manager)

user_question = "项目进展如何？"
prompt = prompt_wrapper.compose_prompt(user_question)

# 传递给 LLM
# llm_response = call_your_llm(prompt)
```

## 🧱 架构

```
greeum/
├── greeum/                # 核心库
│   ├── block_manager.py    # 长期记忆管理
│   ├── stm_manager.py      # 短期记忆管理
│   ├── cache_manager.py    # 路点缓存
│   ├── prompt_wrapper.py   # 提示词组合
│   ├── text_utils.py       # 文本处理工具
│   ├── temporal_reasoner.py # 时间推理
│   ├── embedding_models.py  # 嵌入模型集成
├── api/                   # REST API 接口
├── cli/                   # 命令行工具
├── data/                  # 数据存储目录
├── tests/                 # 测试套件
```

## 分支管理规则

- **main**：稳定发布版本分支
- **dev**：核心功能开发分支（开发和测试后合并到 main）
- **test-collect**：性能指标和 A/B 测试数据收集分支

## 📊 性能测试

Greeum 在以下领域进行性能测试：

### T-GEN-001：响应具体性增加率
- 测量使用 Greeum 记忆时的响应质量改进
- 确认平均 18.6% 质量提升
- 增加 4.2 个具体信息包含

### T-MEM-002：记忆搜索延迟
- 测量通过路点缓存的搜索速度改进
- 确认平均 5.04 倍速度提升
- 对于 1,000+ 记忆区块，速度提升高达 8.67 倍

### T-API-001：API 调用效率
- 测量由于基于记忆的上下文提供而导致的重新询问减少率
- 确认重新询问必要性减少 78.2%
- 由于减少 API 调用而节省成本

## 📊 记忆区块结构

```json
{
  "block_index": 143,
  "timestamp": "2025-05-08T01:02:33",
  "context": "开始了一个新项目，真的很令人兴奋",
  "keywords": ["项目", "开始", "兴奋"],
  "tags": ["积极", "开始", "动力"],
  "embedding": [0.131, 0.847, ...],
  "importance": 0.91,
  "hash": "...",
  "prev_hash": "..."
}
```

## 🔤 支持的语言

Greeum 支持以下语言的时间表达式识别：
- 🇰🇷 韩语：基本支持韩语时间表达式（어제, 지난주, 3일 전 等）
- 🇺🇸 英语：完全支持英语时间格式（yesterday, 3 days ago 等）
- 🇨🇳 中文：支持中文时间表达式（昨天，三天前 等）
- 🌐 自动检测：自动检测语言并相应处理

## 🔍 时间推理示例

```python
# 韩语
result = evaluate_temporal_query("3일 전에 뭐 했어?", language="ko")
# 返回值：{detected: True, language: "ko", best_ref: {term: "3일 전"}}

# 英语
result = evaluate_temporal_query("What did I do 3 days ago?", language="en")
# 返回值：{detected: True, language: "en", best_ref: {term: "3 days ago"}}

# 中文
result = evaluate_temporal_query("我三天前做了什么？", language="zh")
# 返回值：{detected: True, language: "zh", best_ref: {term: "三天前"}}

# 自动检测
result = evaluate_temporal_query("What happened yesterday?")
# 返回值：{detected: True, language: "en", best_ref: {term: "yesterday"}}
```

## 🔧 项目扩展计划

- **模型控制协议**：查看 [GreeumMCP](https://github.com/DryRainEnt/GreeumMCP) 仓库了解 MCP 支持 - 这是一个单独的包，允许 Greeum 与 Cursor、Unity、Discord 等工具连接
- **增强多语言支持**：日语、中文、西班牙语等额外语言支持
- **改进嵌入**：集成实际嵌入模型（例如 sentence-transformers）
- **增强关键词提取**：实现特定语言的关键词提取
- **云集成**：添加数据库后端（SQLite、MongoDB 等）
- **分布式处理**：实现大规模记忆管理的分布式处理

## 🌐 网站

访问网站：[greeum.app](https://greeum.app)

## 📄 许可证

MIT 许可证

## 👥 贡献

欢迎所有贡献，包括错误报告、功能建议、拉取请求等！

## 📱 联系方式

电子邮件：playtart@play-t.art 