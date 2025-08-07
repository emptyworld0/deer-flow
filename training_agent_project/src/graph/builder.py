# Copyright (c) 2025
# SPDX-License-Identifier: MIT

import logging
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
from langchain_core.runnables import RunnableConfig
from typing import Literal

from .types import TrainingAgentState, StepType
from .nodes import (
    coordinator_node,
    planner_node,
    reporter_node
)
from .dynamic_executor import dynamic_executor

logger = logging.getLogger(__name__)

def dynamic_executor_node(state: TrainingAgentState, config: RunnableConfig) -> Command[Literal["dynamic_executor", "reporter"]]:
    """
    动态执行器节点 - 根据计划执行相应的分析步骤
    """
    logger.info("Dynamic executor node is running")
    
    current_plan = state.get("current_plan")
    if not current_plan:
        return Command(goto="reporter", update={"final_report": "Error: No plan found"})
    
    # 获取下一个要执行的步骤
    next_step = dynamic_executor.get_next_step(current_plan)
    if not next_step:
        return Command(goto="reporter", update={})
    
    try:
        # 执行步骤
        logger.info(f"Executing step: {next_step.title} ({next_step.step_type.value})")
        step_result = await dynamic_executor.execute_step(state, config, next_step)
        
        # 更新observations
        observations = state.get("observations", [])
        if "error" not in step_result:
            observations.append(f"Completed step: {next_step.title}")
        else:
            observations.append(f"Failed step: {next_step.title} - {step_result['error']}")
        
        # 合并步骤执行结果到状态
        update_data = {
            "current_plan": current_plan,
            "observations": observations
        }
        update_data.update(step_result)
        
        # 检查是否还有未执行的步骤
        remaining_step = dynamic_executor.get_next_step(current_plan)
        if remaining_step:
            return Command(goto="dynamic_executor", update=update_data)
        else:
            return Command(goto="reporter", update=update_data)
            
    except Exception as e:
        logger.error(f"Error in dynamic executor: {str(e)}")
        next_step.execution_res = f"Error: {str(e)}"
        observations = state.get("observations", [])
        observations.append(f"Failed step: {next_step.title} - {str(e)}")
        
        return Command(goto="reporter", update={
            "current_plan": current_plan,
            "observations": observations
        })


def continue_research_workflow(state: TrainingAgentState) -> Literal["dynamic_executor", "reporter"]:
    """
    决定下一个要执行的研究步骤
    """
    current_plan = state.get("current_plan")
    if not current_plan or not current_plan.steps:
        return "reporter"
    
    # 查找下一个未执行的步骤
    next_step = dynamic_executor.get_next_step(current_plan)
    if next_step:
        return "dynamic_executor"
    
    # 所有步骤都已完成，生成报告
    return "reporter"


def _build_base_graph():
    """构建基础状态图，包含所有节点和连接"""
    builder = StateGraph(TrainingAgentState)
    
    # 添加所有节点
    builder.add_node("coordinator", coordinator_node)
    builder.add_node("planner", planner_node)
    builder.add_node("dynamic_executor", dynamic_executor_node)
    builder.add_node("reporter", reporter_node)
    
    # 定义工作流连接
    builder.add_edge(START, "coordinator")
    
    # 协调器可以直接进入规划器或动态执行器
    # (这个决策在coordinator_node内部通过Command处理)
    
    # 规划器完成后进入动态执行器
    # (通过Command处理)
    
    # 动态执行器的条件性路由
    builder.add_conditional_edges(
        "dynamic_executor",
        continue_research_workflow,
        {
            "dynamic_executor": "dynamic_executor",
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
    训练任务深度研究工作流 (动态执行版本):
    
    START → 协调器 → 规划器 → 动态执行器 ⟲ → 报告器 → END
                   ↑                    ↓
                   └─── 如有现有计划 ────┘
    
    节点说明:
    - 协调器: 解析任务ID，初始化研究流程
    - 规划器: 生成研究计划，包含6+个可配置步骤
    - 动态执行器: 根据计划动态执行相应的分析功能
      * 任务信息收集 (TaskInfoExecutor)
      * 性能分析 (PerformanceAnalysisExecutor) 
      * 资源分析 (ResourceAnalysisExecutor)
      * 日志分析 (LogAnalysisExecutor)
      * 错误诊断 (ErrorDiagnosisExecutor)
      * 优化建议 (OptimizationExecutor)
      * 对比分析 (ComparisonExecutor)
    - 报告器: 生成综合研究报告
    
    优势:
    ✅ 计划步骤 = 执行步骤 (完全一致)
    ✅ 动态执行顺序 (可重排、跳过、添加步骤)
    ✅ 模块化执行器 (易于扩展新的分析类型)
    ✅ RAG增强 (智能诊断和建议)
    ✅ 容错处理 (单步失败不影响整体流程)
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