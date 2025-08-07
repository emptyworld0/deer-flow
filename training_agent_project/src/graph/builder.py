# Copyright (c) 2025
# SPDX-License-Identifier: MIT

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from typing import Literal

from .types import TrainingAgentState, StepType
from .nodes import (
    coordinator_node,
    planner_node,
    task_analyzer_node,
    performance_analyzer_node,
    log_analyzer_node,
    diagnostics_node,
    reporter_node
)


def continue_research_workflow(state: TrainingAgentState) -> Literal["task_analyzer", "performance_analyzer", "log_analyzer", "diagnostics_node", "reporter"]:
    """
    决定下一个要执行的研究步骤
    """
    current_plan = state.get("current_plan")
    if not current_plan or not current_plan.steps:
        return "reporter"
    
    # 查找下一个未执行的步骤
    for step in current_plan.steps:
        if not step.execution_res:
            if step.step_type == StepType.TASK_INFO:
                return "task_analyzer"
            elif step.step_type == StepType.PERFORMANCE_ANALYSIS or step.step_type == StepType.RESOURCE_ANALYSIS:
                return "performance_analyzer"
            elif step.step_type == StepType.LOG_ANALYSIS:
                return "log_analyzer"
            elif step.step_type == StepType.ERROR_DIAGNOSIS or step.step_type == StepType.OPTIMIZATION:
                return "diagnostics_node"
    
    # 所有步骤都已完成，生成报告
    return "reporter"


def _build_base_graph():
    """构建基础状态图，包含所有节点和连接"""
    builder = StateGraph(TrainingAgentState)
    
    # 添加所有节点
    builder.add_node("coordinator", coordinator_node)
    builder.add_node("planner", planner_node)
    builder.add_node("task_analyzer", task_analyzer_node)
    builder.add_node("performance_analyzer", performance_analyzer_node)
    builder.add_node("log_analyzer", log_analyzer_node)
    builder.add_node("diagnostics_node", diagnostics_node)
    builder.add_node("reporter", reporter_node)
    
    # 定义工作流连接
    builder.add_edge(START, "coordinator")
    
    # 协调器可以直接进入规划器或任务分析器
    # (这个决策在coordinator_node内部通过Command处理)
    
    # 规划器完成后进入任务分析器
    # (通过Command处理)
    
    # 条件性路由 - 动态决定下一步
    builder.add_conditional_edges(
        "task_analyzer",
        continue_research_workflow,
        {
            "task_analyzer": "task_analyzer",
            "performance_analyzer": "performance_analyzer",
            "log_analyzer": "log_analyzer",
            "diagnostics_node": "diagnostics_node",
            "reporter": "reporter"
        }
    )
    
    builder.add_conditional_edges(
        "performance_analyzer", 
        continue_research_workflow,
        {
            "task_analyzer": "task_analyzer",
            "performance_analyzer": "performance_analyzer",
            "log_analyzer": "log_analyzer",
            "diagnostics_node": "diagnostics_node",
            "reporter": "reporter"
        }
    )
    
    builder.add_conditional_edges(
        "log_analyzer",
        continue_research_workflow,
        {
            "task_analyzer": "task_analyzer",
            "performance_analyzer": "performance_analyzer", 
            "log_analyzer": "log_analyzer",
            "diagnostics_node": "diagnostics_node",
            "reporter": "reporter"
        }
    )
    
    builder.add_conditional_edges(
        "diagnostics_node",
        continue_research_workflow,
        {
            "task_analyzer": "task_analyzer",
            "performance_analyzer": "performance_analyzer",
            "log_analyzer": "log_analyzer", 
            "diagnostics_node": "diagnostics_node",
            "reporter": "reporter"
        }
    )
    
    # 报告器是终点
    builder.add_edge("reporter", END)
    
    return builder


def build_graph_with_memory():
    """构建带有内存的训练任务研究工作流图"""
    # 使用持久内存保存对话历史
    memory = MemorySaver()
    
    # 构建状态图
    builder = _build_base_graph()
    return builder.compile(checkpointer=memory)


def build_graph():
    """构建不带内存的训练任务研究工作流图"""
    # 构建状态图
    builder = _build_base_graph()
    return builder.compile()


# 默认导出
training_research_graph = build_graph()


def get_workflow_visualization():
    """
    获取工作流的可视化描述
    """
    return """
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
    
    特点:
    - 基于步骤状态的条件路由
    - 自动跳过已完成的步骤
    - 容错处理和错误恢复
    - 模块化和可扩展的设计
    """


if __name__ == "__main__":
    # 测试工作流构建
    print("Building training research workflow...")
    graph = build_graph()
    print("✅ Workflow built successfully!")
    
    # 输出工作流描述
    print(get_workflow_visualization())
    
    # 如果支持，输出Mermaid图
    try:
        mermaid_graph = graph.get_graph().draw_mermaid()
        print("\n=== Mermaid Graph ===")
        print(mermaid_graph)
    except Exception as e:
        print(f"Could not generate Mermaid graph: {e}")