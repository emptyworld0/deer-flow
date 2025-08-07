# 🤖 Training Task Deep Research Agent

基于DeerFlow架构的训练集群专用深度研究Agent系统，专门用于分析和诊断训练任务。

## 🌟 功能特性

### 核心能力
- 🔍 **全面任务分析**: 自动获取训练任务的基本信息、状态和配置
- 📊 **性能深度分析**: 分析训练指标趋势、收敛情况和性能瓶颈
- 🖥️ **资源使用监控**: 监控GPU、CPU、内存和存储资源的使用情况
- 📝 **智能日志分析**: 自动分析训练、错误和系统日志，识别问题
- 🔧 **问题诊断**: 基于AI的问题识别和根因分析
- 💡 **优化建议**: 提供可执行的性能优化和问题解决建议

### 架构特点
- 🏗️ **模块化设计**: 基于LangGraph的状态图工作流
- 🔄 **自适应路由**: 根据任务状态动态调整分析步骤
- 🌊 **流式处理**: 支持实时进度反馈和流式结果输出
- ⚡ **异步执行**: 高性能异步处理，支持并发任务
- 🛡️ **容错机制**: 完善的错误处理和恢复能力

## 🏗️ 系统架构

```
训练任务深度研究工作流:

START → 协调器 → 规划器 → 任务分析器 → 性能分析器 → 日志分析器 → 诊断器 → 报告器 → END
               ↑                    ↓              ↓           ↓         ↓
               └─────────── 条件性循环 ─────────────┴──────────┴─────────┘

节点说明:
- 协调器: 解析任务ID，初始化研究流程
- 规划器: 生成研究计划，包含6个步骤
- 任务分析器: 获取训练任务基本信息
- 性能分析器: 分析训练指标和资源使用
- 日志分析器: 收集和分析各类日志
- 诊断器: 问题诊断和优化建议生成
- 报告器: 生成综合研究报告
```

## 🚀 快速开始

### 环境要求
- Python 3.12+
- 训练集群API访问权限
- 推荐: Docker (用于部署)

### 安装

```bash
# 克隆项目
git clone <repository-url>
cd training-agent

# 安装依赖
pip install -e .

# 开发环境安装 (包含开发工具)
pip install -e ".[dev,llm]"

# 集群环境安装 (包含Kubernetes支持)
pip install -e ".[cluster]"
```

### 配置

创建 `.env` 文件:

```bash
# 集群配置
CLUSTER_API_URL=http://your-cluster-api:8080
CLUSTER_AUTH_TOKEN=your-auth-token

# LLM配置 (可选，用于高级分析)
OPENAI_API_KEY=your-openai-key
# 或其他LLM提供商配置

# 服务配置
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
LOG_LEVEL=INFO
```

### 启动服务

```bash
# 启动FastAPI服务器
python -m src.server.app

# 或使用uvicorn
uvicorn src.server.app:app --host 0.0.0.0 --port 8000 --reload
```

服务启动后，访问:
- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/api/health

## 📖 API使用指南

### 启动深度研究 (流式)

```bash
curl -X POST "http://localhost:8000/api/research/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "train-20241201-001",
    "analysis_depth": "detailed",
    "max_log_lines": 1000,
    "cluster_config": {
      "cluster_api_url": "http://your-cluster:8080",
      "auth_token": "your-token"
    }
  }'
```

### 启动深度研究 (异步)

```bash
curl -X POST "http://localhost:8000/api/research/start" \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "train-20241201-001",
    "analysis_depth": "comprehensive"
  }'
```

### 查询研究状态

```bash
curl "http://localhost:8000/api/research/status/train-20241201-001"
```

### 获取研究报告

```bash
curl "http://localhost:8000/api/research/report/train-20241201-001"
```

## 🔧 高级配置

### 集群API适配

如果您的训练集群使用不同的API格式，可以修改 `src/tools/cluster_tools.py` 中的工具函数:

```python
@tool
def get_training_task_info(task_id: str, cluster_config: Dict[str, Any]) -> Dict[str, Any]:
    """适配您的集群API"""
    # 修改这里的API调用逻辑
    pass
```

### 自定义分析步骤

在 `src/graph/nodes.py` 中可以添加自定义的分析节点:

```python
def custom_analyzer_node(state: TrainingAgentState, config: RunnableConfig) -> Command:
    """自定义分析节点"""
    # 实现您的自定义分析逻辑
    pass
```

### 扩展诊断规则

在 `src/tools/cluster_tools.py` 的 `diagnose_training_issues` 函数中添加自定义诊断规则:

```python
# 检查自定义错误模式
custom_keywords = ["your_custom_error", "specific_issue"]
for log_entry in logs:
    # 添加您的诊断逻辑
    pass
```

## 📊 输出报告示例

```markdown
# Training Task Deep Research Report

## Executive Summary
**Task ID:** train-20241201-001
**Task Name:** BERT Fine-tuning
**Status:** completed
**Model:** bert-base-uncased
**Dataset:** custom_dataset_v2

## Research Execution Results

### 1. Get Basic Task Information
**Type:** task_info
**Status:** ✅ Completed

### 2. Collect Training Metrics
**Type:** performance_analysis
**Status:** ✅ Completed
**Loss Analysis:** decreasing trend, 45.32% improvement
**Accuracy Analysis:** increasing trend, 23.45% improvement

## Performance Summary
**Loss Performance:**
- Initial: 2.834
- Final: 1.549
- Trend: decreasing
- Improvement: 45.32%

**Accuracy Performance:**
- Initial: 0.712
- Final: 0.879
- Trend: increasing
- Improvement: 23.45%

## Resource Usage Summary
- **GPU:** 7.2/8.0 GB (90.0%)
- **CPU:** 12.5/16.0 cores (78.1%)
- **MEMORY:** 28.3/32.0 GB (88.4%)

## Conclusion
✅ Training task completed successfully.
```

## 🧪 测试

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/

# 生成覆盖率报告
pytest --cov=src --cov-report=html
```

## 🔍 监控和日志

### 日志配置

系统使用结构化日志，支持多种日志级别:

```python
import logging
logger = logging.getLogger(__name__)

# 不同级别的日志
logger.debug("详细调试信息")
logger.info("一般信息")
logger.warning("警告信息")
logger.error("错误信息")
logger.critical("严重错误")
```

### 监控指标

如果安装了监控组件 (`pip install -e ".[monitoring]"`):

- 请求数量和延迟
- 任务执行时间
- 错误率和成功率
- 资源使用情况

## 🐳 Docker部署

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . .

RUN pip install -e .

EXPOSE 8000

CMD ["uvicorn", "src.server.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

构建和运行:

```bash
docker build -t training-agent .
docker run -p 8000:8000 -e CLUSTER_API_URL=http://your-cluster:8080 training-agent
```

## 🤝 贡献指南

1. Fork项目
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开Pull Request

### 代码规范

```bash
# 代码格式化
black src/ tests/
isort src/ tests/

# 类型检查
mypy src/

# 代码检查
flake8 src/ tests/
```

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

本项目基于以下优秀的开源项目:

- [DeerFlow](https://github.com/bytedance/deer-flow) - 深度研究框架
- [LangGraph](https://github.com/langchain-ai/langgraph) - 状态图工作流
- [FastAPI](https://fastapi.tiangolo.com/) - 现代Web框架
- [LangChain](https://langchain.com/) - LLM应用开发框架

## 📞 支持

如果您有任何问题或建议:

- 📧 邮箱: team@example.com  
- 🐛 Bug报告: [GitHub Issues](https://github.com/your-org/training-agent/issues)
- 💬 讨论: [GitHub Discussions](https://github.com/your-org/training-agent/discussions)

---

**Happy Training! 🚀**