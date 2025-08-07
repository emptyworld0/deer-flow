#!/usr/bin/env python3
"""
Training Task Deep Research Agent - 动态执行系统示例

本示例展示新的动态执行系统如何根据规划器生成的计划动态执行分析步骤。
"""

import asyncio
import json
from datetime import datetime

from src.graph.types import (
    TrainingAgentState, 
    TrainingPlan, 
    TrainingResearchStep, 
    StepType
)
from src.graph.dynamic_executor import (
    DynamicStepExecutor,
    TaskInfoExecutor,
    PerformanceAnalysisExecutor,
    ResourceAnalysisExecutor,
    LogAnalysisExecutor,
    ErrorDiagnosisExecutor,
    OptimizationExecutor
)
from src.graph.builder import build_graph, get_workflow_visualization


def create_sample_plan(task_id: str) -> TrainingPlan:
    """创建示例研究计划"""
    return TrainingPlan(
        locale="zh-CN",
        has_enough_context=False,
        thought=f"为了全面分析训练任务 {task_id}，我们需要收集性能、资源、日志等全方位信息",
        title=f"训练任务 {task_id} 深度分析计划",
        steps=[
            TrainingResearchStep(
                need_cluster_access=True,
                title="获取任务基本信息",
                description=f"收集训练任务 {task_id} 的基本信息，包括状态、模型、数据集等",
                step_type=StepType.TASK_INFO
            ),
            TrainingResearchStep(
                need_cluster_access=True,
                title="性能指标分析",
                description=f"分析训练任务 {task_id} 的损失、准确率等性能指标趋势",
                step_type=StepType.PERFORMANCE_ANALYSIS
            ),
            TrainingResearchStep(
                need_cluster_access=True,
                title="资源使用分析",
                description=f"监控训练任务 {task_id} 的GPU、CPU、内存等资源使用情况",
                step_type=StepType.RESOURCE_ANALYSIS
            ),
            TrainingResearchStep(
                need_cluster_access=True,
                title="日志分析",
                description=f"分析训练任务 {task_id} 的训练日志、错误日志和系统日志",
                step_type=StepType.LOG_ANALYSIS
            ),
            TrainingResearchStep(
                need_cluster_access=False,
                title="错误诊断",
                description=f"对训练任务 {task_id} 进行问题诊断和根因分析",
                step_type=StepType.ERROR_DIAGNOSIS
            ),
            TrainingResearchStep(
                need_cluster_access=False,
                title="优化建议",
                description=f"为训练任务 {task_id} 生成性能优化和问题解决建议",
                step_type=StepType.OPTIMIZATION
            )
        ]
    )


def create_sample_state(task_id: str, plan: TrainingPlan) -> TrainingAgentState:
    """创建示例状态"""
    return TrainingAgentState(
        messages=[{"role": "user", "content": task_id}],
        task_id=task_id,
        research_topic=f"Deep analysis of training task {task_id}",
        current_plan=plan,
        observations=[],
        training_metrics=[],
        resource_usage=[],
        error_logs=[],
        performance_data={},
        cluster_info={},
        locale="zh-CN",
        enable_detailed_analysis=True,
        max_log_lines=1000,
        analysis_depth="detailed"
    )


def create_mock_config():
    """创建模拟配置"""
    return {
        "configurable": {
            "thread_id": "test_thread",
            "cluster_api_url": "http://localhost:8080",
            "auth_token": None,
            "timeout": 30
        },
        "recursion_limit": 50
    }


async def demo_step_by_step_execution():
    """演示逐步执行流程"""
    print("🚀 动态执行系统 - 逐步执行演示")
    print("=" * 60)
    
    # 创建测试数据
    task_id = "demo-task-001"
    plan = create_sample_plan(task_id)
    state = create_sample_state(task_id, plan)
    config = create_mock_config()
    
    print(f"📋 任务ID: {task_id}")
    print(f"📝 研究计划: {plan.title}")
    print(f"📊 总步骤数: {len(plan.steps)}")
    
    # 创建动态执行器
    executor = DynamicStepExecutor()
    
    print(f"\n🔄 开始逐步执行计划...")
    
    step_num = 1
    while True:
        # 获取下一个要执行的步骤
        next_step = executor.get_next_step(plan)
        if not next_step:
            print(f"\n✅ 所有步骤执行完成!")
            break
        
        print(f"\n--- 步骤 {step_num}: {next_step.title} ---")
        print(f"类型: {next_step.step_type.value}")
        print(f"描述: {next_step.description}")
        print(f"需要集群访问: {'是' if next_step.need_cluster_access else '否'}")
        
        try:
            # 执行步骤 (这里会失败，因为没有真实的集群API)
            print("🔧 执行中...")
            result = await executor.execute_step(state, config, next_step)
            
            if "error" in result:
                print(f"❌ 执行失败: {result['error']}")
                # 模拟标记为已执行 (错误)
                next_step.execution_res = f"Error: {result['error']}"
            else:
                print(f"✅ 执行成功")
                print(f"结果键: {list(result.keys())}")
                # 更新状态
                for key, value in result.items():
                    if hasattr(state, key):
                        setattr(state, key, value)
        
        except Exception as e:
            print(f"❌ 执行异常: {str(e)}")
            next_step.execution_res = f"Exception: {str(e)}"
        
        step_num += 1
        
        # 为了演示，最多执行3步
        if step_num > 3:
            print(f"\n⏸️ 演示限制，停止执行")
            break
    
    # 显示执行结果摘要
    print(f"\n📊 执行结果摘要:")
    executed_count = sum(1 for step in plan.steps if step.execution_res)
    print(f"- 已执行步骤: {executed_count}/{len(plan.steps)}")
    print(f"- 收集的观察: {len(state.observations)}")
    print(f"- 当前状态: {state.analysis_depth} 分析模式")


async def demo_executor_types():
    """演示不同类型的执行器"""
    print("\n🧩 执行器类型演示")
    print("=" * 60)
    
    # 创建各种执行器
    executors = {
        "任务信息": TaskInfoExecutor(),
        "性能分析": PerformanceAnalysisExecutor(), 
        "资源分析": ResourceAnalysisExecutor(),
        "日志分析": LogAnalysisExecutor(),
        "错误诊断": ErrorDiagnosisExecutor(),
        "优化建议": OptimizationExecutor()
    }
    
    print(f"📦 可用执行器类型:")
    for name, executor in executors.items():
        print(f"- {name}: {executor.__class__.__name__} (类型: {executor.step_type.value})")
    
    print(f"\n🔄 执行器映射关系:")
    dynamic_executor = DynamicStepExecutor()
    for step_type, executor in dynamic_executor.executors.items():
        print(f"- {step_type.value} → {executor.__class__.__name__}")


async def demo_plan_customization():
    """演示计划定制化"""
    print("\n⚙️ 计划定制化演示")
    print("=" * 60)
    
    # 创建自定义计划
    custom_plan = TrainingPlan(
        locale="zh-CN",
        has_enough_context=False,
        thought="这是一个定制化的分析计划，专注于特定问题",
        title="自定义深度分析计划",
        steps=[
            TrainingResearchStep(
                need_cluster_access=True,
                title="快速任务检查",
                description="快速检查任务状态和基本信息",
                step_type=StepType.TASK_INFO
            ),
            TrainingResearchStep(
                need_cluster_access=True,
                title="重点性能分析",
                description="重点关注损失函数和收敛性分析",
                step_type=StepType.PERFORMANCE_ANALYSIS
            ),
            TrainingResearchStep(
                need_cluster_access=False,
                title="问题诊断",
                description="基于性能数据进行问题诊断",
                step_type=StepType.ERROR_DIAGNOSIS
            ),
            # 可以添加对比分析
            TrainingResearchStep(
                need_cluster_access=False,
                title="与历史任务对比",
                description="与历史相似任务进行对比分析",
                step_type=StepType.COMPARISON
            )
        ]
    )
    
    print(f"📋 定制计划: {custom_plan.title}")
    print(f"🧠 分析思路: {custom_plan.thought}")
    print(f"📝 包含步骤:")
    
    for i, step in enumerate(custom_plan.steps, 1):
        print(f"  {i}. {step.title} ({step.step_type.value})")
        print(f"     {step.description}")
    
    print(f"\n✨ 优势:")
    print(f"- ✅ 可以跳过不需要的步骤")
    print(f"- ✅ 可以重新排序步骤")
    print(f"- ✅ 可以添加新的分析类型")
    print(f"- ✅ 支持条件执行")


async def demo_workflow_comparison():
    """演示新旧工作流对比"""
    print("\n🔄 新旧工作流对比")
    print("=" * 60)
    
    print(f"🔴 旧版本问题:")
    print(f"- 固定节点序列: task_analyzer → performance_analyzer → log_analyzer → diagnostics")
    print(f"- 计划步骤与执行节点不匹配")
    print(f"- 难以跳过或重排步骤")
    print(f"- 新增分析类型需要修改工作流图")
    
    print(f"\n🟢 新版本优势:")
    print(f"- 动态执行: 根据计划执行相应步骤")
    print(f"- 计划驱动: 计划步骤 = 执行步骤")
    print(f"- 高度灵活: 可以任意重排、跳过、添加步骤")
    print(f"- 易于扩展: 新增执行器即可支持新分析类型")
    
    print(f"\n📊 架构对比:")
    print(f"旧版本: 规划器(6步) → 固定4个节点")
    print(f"新版本: 规划器(N步) → 动态执行器(N个执行器)")
    
    print(f"\n🎯 典型场景:")
    scenarios = [
        ("快速检查", ["task_info", "performance_analysis"]),
        ("问题诊断", ["task_info", "log_analysis", "error_diagnosis"]),
        ("全面分析", ["task_info", "performance_analysis", "resource_analysis", "log_analysis", "error_diagnosis", "optimization"]),
        ("对比研究", ["task_info", "performance_analysis", "comparison"])
    ]
    
    for scenario, steps in scenarios:
        print(f"- {scenario}: {' → '.join(steps)}")


async def demo_error_handling():
    """演示错误处理"""
    print("\n🛡️ 错误处理演示")
    print("=" * 60)
    
    # 创建测试计划
    task_id = "error-demo-task"
    plan = create_sample_plan(task_id)
    state = create_sample_state(task_id, plan)
    config = create_mock_config()
    
    executor = DynamicStepExecutor()
    
    print(f"📋 模拟步骤执行中的各种错误情况...")
    
    # 模拟第一步成功
    step1 = plan.steps[0]
    print(f"\n1️⃣ {step1.title}")
    step1.execution_res = json.dumps({"task_id": task_id, "status": "running", "model": "bert"})
    print(f"   ✅ 执行成功")
    
    # 模拟第二步失败
    step2 = plan.steps[1]
    print(f"\n2️⃣ {step2.title}")
    step2.execution_res = "Error: Failed to connect to metrics API"
    print(f"   ❌ 执行失败: 连接指标API失败")
    
    # 模拟第三步跳过
    step3 = plan.steps[2]
    print(f"\n3️⃣ {step3.title}")
    step3.execution_res = "Skipped: Resource analysis not available"
    print(f"   ⏭️ 跳过执行: 资源分析不可用")
    
    # 模拟第四步成功
    step4 = plan.steps[3]
    print(f"\n4️⃣ {step4.title}")
    step4.execution_res = json.dumps({"logs": ["info: training started", "error: loss spike detected"]})
    print(f"   ✅ 执行成功")
    
    print(f"\n📊 容错特点:")
    print(f"- ✅ 单步失败不影响其他步骤")
    print(f"- ✅ 可以选择性跳过步骤")
    print(f"- ✅ 失败信息被记录用于报告")
    print(f"- ✅ 部分结果也能生成有价值的报告")
    
    # 检查剩余步骤
    remaining = executor.get_next_step(plan)
    if remaining:
        print(f"- ⏭️ 下一步: {remaining.title}")
    else:
        print(f"- 🏁 所有步骤已处理")


async def main():
    """主演示函数"""
    print("🤖 Training Task Deep Research Agent - 动态执行系统演示")
    print("=" * 80)
    
    # 显示工作流架构
    print("🏗️ 新架构可视化:")
    print(get_workflow_visualization())
    
    try:
        # 运行各种演示
        await demo_step_by_step_execution()
        await demo_executor_types()
        await demo_plan_customization()
        await demo_workflow_comparison()
        await demo_error_handling()
        
        print(f"\n🎉 动态执行系统演示完成!")
        print(f"\n📝 总结:")
        print(f"✅ 计划驱动的执行系统")
        print(f"✅ 高度模块化和可扩展")
        print(f"✅ 灵活的步骤组合")
        print(f"✅ 完善的错误处理")
        print(f"✅ RAG增强的智能分析")
        
    except Exception as e:
        print(f"\n❌ 演示执行失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())