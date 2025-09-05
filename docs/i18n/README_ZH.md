# 🧠 Greeum v2.2.5

<p align="center">
  <a href="../../README.md">🇰🇷 한국어</a> |
  <a href="README_EN.md">🇺🇸 English</a> |
  <a href="README_JP.md">🇯🇵 日本語</a> |
  <a href="README_ZH.md">🇨🇳 中文</a>
</p>

面向LLM的智能记忆管理系统

## 📌 概述

**Greeum**（发音：格里乌姆）是一个可以连接任何LLM（大语言模型）的**通用记忆模块**：

- **长期记忆**: 用户上下文、偏好和目标的永久存储
- **短期记忆**: 基于会话的重要信息管理  
- **智能搜索**: 基于上下文的自动记忆回忆
- **质量管理**: 自动记忆质量验证和优化
- **多语言支持**: 完全支持韩语、英语、日语、中文

"Greeum"这个名字来源于韩语"그리움"（思念/怀念），象征着AI记住过去并对其怀念的能力。

## 🚀 快速开始

### 安装

```bash
# 使用pipx安装（推荐）
pipx install greeum>=2.2.5

# 或使用pip安装
pip install greeum>=2.2.5
```

### 基本用法

```bash
# 添加记忆
greeum memory add "今天开始了一个新项目。计划用Python开发Web应用程序。"

# 设置记忆锚点（v2.2.5+新功能）
greeum anchors set A 123  # 将重要记忆固定到插槽A

# 基于锚点的搜索
greeum memory search "项目 Python" --slot A --radius 3

# 查看锚点状态
greeum anchors status

# 长期记忆分析
greeum ltm analyze --period 30d --trends

# 添加短期记忆
greeum stm add "临时备忘" --ttl 1h

# 运行MCP服务器
greeum mcp serve
```

## 🔑 主要功能

### 📚 多层记忆系统
- **LTM（长期记忆）**: 使用区块链式结构的永久存储
- **STM（短期记忆）**: 基于TTL的临时记忆管理
- **航点缓存**: 自动加载上下文相关记忆

### 🧠 智能记忆管理
- **质量验证**: 基于7个指标的自动质量评估
- **重复检测**: 85%相似度阈值防重复
- **使用分析**: 模式分析和优化建议
- **自动清理**: 基于质量的记忆清理

### 🔍 高级搜索
- **关键词搜索**: 基于标签和关键词的搜索
- **向量搜索**: 语义相似度搜索
- **时间搜索**: "3天前"、"上周"等自然语言时间表达
- **锚点搜索**: 以固定点为中心的局部化搜索（v2.2.5+）
- **混合搜索**: 关键词 + 向量 + 时间 + 锚点的组合搜索

### ⚓ 锚点系统（v2.2.5新功能）
- **记忆锚点**: 将重要记忆固定到A-Z插槽
- **锁定功能**: 防止或允许锚点自动移动
- **局部化搜索**: 快速搜索锚点周围的相关记忆
- **自动优化**: 基于使用模式的锚点自动调整

### 🌐 MCP集成
- **Claude Code**: 与12个MCP工具完全集成
- **实时同步**: 记忆创建/搜索的实时反映
- **质量验证**: 自动质量检查和反馈

## 🛠️ 高级用法

### API使用
```python
from greeum import BlockManager, STMManager, PromptWrapper

# 初始化记忆系统
bm = BlockManager()
stm = STMManager()
pw = PromptWrapper()

# 添加记忆
bm.add_block(
    context="重要的会议内容",
    keywords=["会议", "决定"],
    importance=0.9
)

# 生成基于上下文的提示
enhanced_prompt = pw.compose_prompt("上次会议我们决定了什么？")
```

### 锚点系统使用（v2.2.5+）
```bash
# 查看锚点状态
greeum anchors status

# 将重要记忆设置为锚点
greeum anchors set A 123    # 将记忆#123设置到插槽A
greeum anchors set B 456    # 将记忆#456设置到插槽B

# 锚点周围搜索
greeum memory search "会议内容" --slot A --radius 3

# 锁定/解锁锚点
greeum anchors pin A        # 防止A自动移动
greeum anchors unpin A      # 允许A自动移动

# 清除锚点
greeum anchors clear A      # 清除插槽A
```

### MCP工具（Claude Code用）
```
可用工具:
- add_memory: 添加新记忆
- search_memory: 搜索记忆
- get_memory_stats: 记忆统计
- ltm_analyze: 长期记忆分析
- stm_add: 添加短期记忆
- quality_check: 质量验证
- check_duplicates: 重复检查
- usage_analytics: 使用分析
- ltm_verify: 完整性验证
- ltm_export: 数据导出
- stm_promote: STM→LTM提升
- stm_cleanup: STM清理
```

## 📊 记忆质量管理

Greeum v2.2.5提供智能质量管理系统和锚点系统：

### 质量评估指标
1. **长度**: 适当的信息量
2. **丰富度**: 有意义词汇的比例
3. **结构**: 句子/段落构成
4. **语言**: 语法和表达质量
5. **信息密度**: 具体信息包含度
6. **可搜索性**: 未来搜索的便利性
7. **时间相关性**: 与当前上下文的相关性

### 自动优化
- **基于质量的重要度调整**
- **自动重复记忆检测**
- **STM→LTM提升建议**
- **基于使用模式的建议**

## 🔗 集成指南

### Claude Code MCP设置
1. **检查安装**
   ```bash
   greeum --version  # v2.2.5或更高版本
   ```

2. **Claude Desktop配置**
   ```json
   {
     "mcpServers": {
       "greeum": {
         "command": "python3",
         "args": ["-m", "greeum.mcp.claude_code_mcp_server"],
         "env": {
           "GREEUM_DATA_DIR": "/path/to/data"
         }
       }
     }
   }
   ```

3. **验证连接**
   ```bash
   claude mcp list  # 检查greeum服务器
   ```

### 其他LLM集成
```python
# OpenAI GPT
from greeum.client import MemoryClient
client = MemoryClient(llm_type="openai")

# 本地LLM
client = MemoryClient(llm_type="local", endpoint="http://localhost:8080")
```

## 📈 性能与基准测试

- **响应质量**: 平均提升18.6%（基准测试）
- **搜索速度**: 提升5.04倍（应用航点缓存）
- **重复提问减少**: 减少78.2%（上下文理解提升）
- **内存效率**: 内存使用优化50%

## 📚 文档与资源

- **[入门指南](../get-started.md)**: 详细安装和配置指南
- **[API参考](../api-reference.md)**: 完整API参考
- **[教程](../tutorials.md)**: 分步使用示例
- **[开发者指南](../developer_guide.md)**: 如何贡献

## 🤝 贡献

Greeum是一个开源项目。欢迎贡献！

### 如何贡献
1. **问题报告**: 发现错误或问题时报告
2. **功能建议**: 新想法和改进建议
3. **代码贡献**: 欢迎提交Pull Request
4. **文档**: 翻译和改进

### 开发环境设置
```bash
# 下载源代码后
pip install -e .[dev]
tox  # 运行测试
```

## 📞 支持与联系

- **📧 官方邮箱**: playtart@play-t.art
- **🌐 官方网站**: [greeum.app](https://greeum.app)
- **📚 文档**: 参考此README和docs/文件夹

## 📄 许可证

本项目在MIT许可证下分发。详情请参见[LICENSE](../../LICENSE)文件。

## 🏆 致谢

- **OpenAI**: 嵌入API支持
- **Anthropic**: Claude MCP平台
- **NumPy**: 高效向量计算
- **SQLite**: 可靠的数据存储

---

<p align="center">
  Made with ❤️ by the Greeum Team<br>
  <em>"通过记忆让AI更加人性化"</em>
</p>