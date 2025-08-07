# Copyright (c) 2025
# SPDX-License-Identifier: MIT

import json
import logging
from typing import Dict, Any, List, Literal
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command
from pydantic import BaseModel

from .types import TrainingAgentState, TrainingPlan, StepType, TrainingResearchStep
from ..tools.cluster_tools import (
    get_training_task_info,
    get_training_metrics, 
    get_resource_usage,
    get_training_logs,
    analyze_training_performance,
    diagnose_training_issues,
    compare_training_tasks
)
from ..rag.knowledge_retriever import create_knowledge_retriever, KnowledgeRetriever

logger = logging.getLogger(__name__)


def coordinator_node(state: TrainingAgentState, config: RunnableConfig) -> Command[Literal["dynamic_executor", "planner"]]:
    """
    协调器节点 - 接收任务ID并决定下一步操作
    """
    logger.info("Training coordinator node is running")
    
    # 从消息中提取任务ID
    messages = state.get("messages", [])
    if not messages:
        return Command(
            goto="__end__",
            update={"messages": [AIMessage(content="Error: No task ID provided")]}
        )
    
    user_message = messages[-1].get("content", "") if messages else ""
    
    # 简单解析任务ID (可以根据实际情况调整)
    task_id = ""
    if "task_id:" in user_message:
        task_id = user_message.split("task_id:")[-1].strip()
    elif user_message.startswith("task-") or user_message.startswith("train-"):
        task_id = user_message.strip()
    else:
        # 假设整个消息就是任务ID
        task_id = user_message.strip()
    
    if not task_id:
        return Command(
            goto="__end__",
            update={"messages": [AIMessage(content="Error: Could not extract task ID from input")]}
        )
    
    research_topic = f"Deep analysis of training task {task_id}"
    
    update_data = {
        "task_id": task_id,
        "research_topic": research_topic,
        "messages": state["messages"] + [
            AIMessage(content=f"Starting deep research for training task: {task_id}")
        ]
    }
    
    # 决定是否已有足够上下文
    if state.get("training_task") and state.get("current_plan"):
        return Command(goto="dynamic_executor", update=update_data)
    else:
        return Command(goto="planner", update=update_data)


def planner_node(state: TrainingAgentState, config: RunnableConfig) -> Command[Literal["dynamic_executor", "__end__"]]:
    """
    规划器节点 - 生成训练任务研究计划
    """
    logger.info("Training planner node is running")
    
    task_id = state.get("task_id", "")
    if not task_id:
        return Command(
            goto="__end__",
            update={"messages": state["messages"] + [AIMessage(content="Error: No task ID provided to planner")]}
        )
    
    # 生成研究计划
    plan = TrainingPlan(
        locale=state.get("locale", "en-US"),
        has_enough_context=False,
        thought=f"To thoroughly analyze training task {task_id}, we need to collect comprehensive information about its performance, resource usage, logs, and identify any issues.",
        title=f"Training Task {task_id} Deep Analysis Plan",
        steps=[
            TrainingResearchStep(
                need_cluster_access=True,
                title="Get Basic Task Information",
                description=f"Retrieve basic information about training task {task_id} including status, model details, and configuration",
                step_type=StepType.TASK_INFO
            ),
            TrainingResearchStep(
                need_cluster_access=True,
                title="Collect Training Metrics",
                description=f"Gather performance metrics including loss, accuracy, and learning rate progression for task {task_id}",
                step_type=StepType.PERFORMANCE_ANALYSIS
            ),
            TrainingResearchStep(
                need_cluster_access=True,
                title="Analyze Resource Usage",
                description=f"Examine GPU, CPU, memory, and storage utilization patterns for task {task_id}",
                step_type=StepType.RESOURCE_ANALYSIS
            ),
            TrainingResearchStep(
                need_cluster_access=True,
                title="Review Training Logs",
                description=f"Analyze training, error, and system logs to identify potential issues for task {task_id}",
                step_type=StepType.LOG_ANALYSIS
            ),
            TrainingResearchStep(
                need_cluster_access=False,
                title="Diagnose Issues and Performance",
                description=f"Perform comprehensive analysis to identify issues, bottlenecks, and optimization opportunities for task {task_id}",
                step_type=StepType.ERROR_DIAGNOSIS
            ),
            TrainingResearchStep(
                need_cluster_access=False,
                title="Generate Optimization Recommendations",
                description=f"Provide actionable recommendations for improving training performance and resolving issues for task {task_id}",
                step_type=StepType.OPTIMIZATION
            )
        ]
    )
    
    update_data = {
        "current_plan": plan,
        "plan_iterations": state.get("plan_iterations", 0) + 1,
        "messages": state["messages"] + [
            AIMessage(content=f"Generated research plan with {len(plan.steps)} steps for task {task_id}")
        ]
    }
    
    return Command(goto="dynamic_executor", update=update_data)


def task_analyzer_node(state: TrainingAgentState, config: RunnableConfig) -> Command[Literal["performance_analyzer", "log_analyzer", "reporter"]]:
    """
    任务分析器节点 - 获取基本任务信息
    """
    logger.info("Task analyzer node is running")
    
    task_id = state.get("task_id", "")
    plan = state.get("current_plan")
    
    if not task_id or not plan:
        return Command(goto="reporter", update={"final_report": "Error: Missing task ID or plan"})
    
    # 查找需要执行的步骤
    current_step = None
    for step in plan.steps:
        if not step.execution_res and step.step_type == StepType.TASK_INFO:
            current_step = step
            break
    
    if not current_step:
        # 任务信息步骤已完成，继续到性能分析
        return Command(goto="performance_analyzer", update={})
    
    # 模拟集群配置 (实际使用时应从配置文件读取)
    cluster_config = {
        "cluster_api_url": config.get("configurable", {}).get("cluster_api_url", "http://localhost:8080"),
        "auth_token": config.get("configurable", {}).get("auth_token")
    }
    
    try:
        # 获取任务基本信息
        task_info_result = get_training_task_info.invoke({
            "task_id": task_id,
            "cluster_config": cluster_config
        })
        
        if "error" in task_info_result:
            error_msg = f"Failed to get task info: {task_info_result['error']}"
            current_step.execution_res = error_msg
        else:
            current_step.execution_res = json.dumps(task_info_result, ensure_ascii=False)
            
            # 解析任务信息到状态
            from .types import TrainingTask, TrainingStatus
            training_task = TrainingTask(
                task_id=task_info_result.get("task_id", task_id),
                name=task_info_result.get("name", f"Task {task_id}"),
                status=TrainingStatus(task_info_result.get("status", "unknown")),
                model_name=task_info_result.get("model_name"),
                dataset_name=task_info_result.get("dataset_name"),
                description=task_info_result.get("description")
            )
        
        observations = state.get("observations", [])
        observations.append(f"Retrieved basic information for task {task_id}")
        
        update_data = {
            "current_plan": plan,
            "training_task": training_task if "error" not in task_info_result else None,
            "observations": observations,
            "cluster_info": {"api_url": cluster_config["cluster_api_url"]}
        }
        
        return Command(goto="performance_analyzer", update=update_data)
        
    except Exception as e:
        logger.error(f"Error in task analyzer: {str(e)}")
        current_step.execution_res = f"Error: {str(e)}"
        return Command(goto="reporter", update={"current_plan": plan})


def performance_analyzer_node(state: TrainingAgentState, config: RunnableConfig) -> Command[Literal["log_analyzer", "reporter"]]:
    """
    性能分析器节点 - 分析训练性能和资源使用
    """
    logger.info("Performance analyzer node is running")
    
    task_id = state.get("task_id", "")
    plan = state.get("current_plan")
    
    if not task_id or not plan:
        return Command(goto="reporter", update={"final_report": "Error: Missing task ID or plan"})
    
    # 查找性能分析步骤
    perf_step = None
    resource_step = None
    
    for step in plan.steps:
        if not step.execution_res and step.step_type == StepType.PERFORMANCE_ANALYSIS:
            perf_step = step
        elif not step.execution_res and step.step_type == StepType.RESOURCE_ANALYSIS:
            resource_step = step
    
    if not perf_step and not resource_step:
        return Command(goto="log_analyzer", update={})
    
    cluster_config = {
        "cluster_api_url": config.get("configurable", {}).get("cluster_api_url", "http://localhost:8080"),
        "auth_token": config.get("configurable", {}).get("auth_token")
    }
    
    try:
        observations = state.get("observations", [])
        
        # 执行性能分析步骤
        if perf_step:
            metrics_result = get_training_metrics.invoke({
                "task_id": task_id,
                "cluster_config": cluster_config
            })
            
            if isinstance(metrics_result, list) and len(metrics_result) > 0 and "error" not in metrics_result[0]:
                # 分析性能数据
                analysis_result = analyze_training_performance.invoke({
                    "task_id": task_id,
                    "metrics_data": metrics_result
                })
                
                perf_step.execution_res = json.dumps({
                    "metrics": metrics_result,
                    "analysis": analysis_result
                }, ensure_ascii=False)
                
                observations.append(f"Analyzed {len(metrics_result)} performance metrics for task {task_id}")
                
                # 存储到状态
                from .types import TrainingMetrics
                training_metrics = []
                for metric in metrics_result:
                    training_metrics.append(TrainingMetrics(
                        loss=metric.get("loss"),
                        accuracy=metric.get("accuracy"),
                        learning_rate=metric.get("learning_rate"),
                        epoch=metric.get("epoch"),
                        step=metric.get("step")
                    ))
            else:
                error_msg = "Failed to retrieve training metrics"
                if metrics_result and "error" in str(metrics_result):
                    error_msg = f"Metrics error: {metrics_result}"
                perf_step.execution_res = error_msg
        
        # 执行资源分析步骤
        if resource_step:
            resource_result = get_resource_usage.invoke({
                "task_id": task_id,
                "cluster_config": cluster_config
            })
            
            if isinstance(resource_result, list) and len(resource_result) > 0 and "error" not in resource_result[0]:
                resource_step.execution_res = json.dumps(resource_result, ensure_ascii=False)
                observations.append(f"Collected resource usage data for task {task_id}")
                
                # 存储到状态
                from .types import ResourceUsage, ResourceType
                resource_usage = []
                for resource in resource_result:
                    resource_usage.append(ResourceUsage(
                        resource_type=ResourceType(resource.get("resource_type", "unknown")),
                        current_usage=resource.get("current_usage", 0),
                        max_usage=resource.get("max_usage", 0),
                        unit=resource.get("unit", "")
                    ))
            else:
                error_msg = "Failed to retrieve resource usage data"
                if resource_result and "error" in str(resource_result):
                    error_msg = f"Resource error: {resource_result}"
                resource_step.execution_res = error_msg
        
        update_data = {
            "current_plan": plan,
            "observations": observations,
            "training_metrics": training_metrics if 'training_metrics' in locals() else state.get("training_metrics", []),
            "resource_usage": resource_usage if 'resource_usage' in locals() else state.get("resource_usage", []),
            "performance_data": analysis_result if 'analysis_result' in locals() else {}
        }
        
        return Command(goto="log_analyzer", update=update_data)
        
    except Exception as e:
        logger.error(f"Error in performance analyzer: {str(e)}")
        if perf_step:
            perf_step.execution_res = f"Error: {str(e)}"
        if resource_step:
            resource_step.execution_res = f"Error: {str(e)}"
        return Command(goto="log_analyzer", update={"current_plan": plan})


def log_analyzer_node(state: TrainingAgentState, config: RunnableConfig) -> Command[Literal["diagnostics_node", "reporter"]]:
    """
    日志分析器节点 - 分析训练日志
    """
    logger.info("Log analyzer node is running")
    
    task_id = state.get("task_id", "")
    plan = state.get("current_plan")
    
    if not task_id or not plan:
        return Command(goto="reporter", update={"final_report": "Error: Missing task ID or plan"})
    
    # 查找日志分析步骤
    log_step = None
    for step in plan.steps:
        if not step.execution_res and step.step_type == StepType.LOG_ANALYSIS:
            log_step = step
            break
    
    if not log_step:
        return Command(goto="diagnostics_node", update={})
    
    cluster_config = {
        "cluster_api_url": config.get("configurable", {}).get("cluster_api_url", "http://localhost:8080"),
        "auth_token": config.get("configurable", {}).get("auth_token")
    }
    
    try:
        # 获取不同类型的日志
        log_types = ["training", "error", "system"]
        all_logs = {}
        
        for log_type in log_types:
            log_result = get_training_logs.invoke({
                "task_id": task_id,
                "cluster_config": cluster_config,
                "log_type": log_type,
                "max_lines": state.get("max_log_lines", 1000)
            })
            
            if "error" not in log_result:
                all_logs[log_type] = log_result.get("logs", [])
            else:
                all_logs[log_type] = {"error": log_result["error"]}
        
        log_step.execution_res = json.dumps(all_logs, ensure_ascii=False)
        
        observations = state.get("observations", [])
        observations.append(f"Analyzed training logs for task {task_id}")
        
        # 提取错误日志
        error_logs = []
        if "error" in all_logs and isinstance(all_logs["error"], list):
            error_logs = [log.get("message", "") for log in all_logs["error"]]
        
        update_data = {
            "current_plan": plan,
            "observations": observations,
            "error_logs": error_logs
        }
        
        return Command(goto="diagnostics_node", update=update_data)
        
    except Exception as e:
        logger.error(f"Error in log analyzer: {str(e)}")
        log_step.execution_res = f"Error: {str(e)}"
        return Command(goto="diagnostics_node", update={"current_plan": plan})


def diagnostics_node(state: TrainingAgentState, config: RunnableConfig) -> Command[Literal["reporter"]]:
    """
    诊断节点 - 进行问题诊断和优化建议（集成RAG）
    """
    logger.info("Diagnostics node is running with RAG integration")
    
    task_id = state.get("task_id", "")
    plan = state.get("current_plan")
    
    if not task_id or not plan:
        return Command(goto="reporter", update={"final_report": "Error: Missing task ID or plan"})
    
    # 查找诊断和优化步骤
    diag_step = None
    opt_step = None
    
    for step in plan.steps:
        if not step.execution_res and step.step_type == StepType.ERROR_DIAGNOSIS:
            diag_step = step
        elif not step.execution_res and step.step_type == StepType.OPTIMIZATION:
            opt_step = step
    
    try:
        observations = state.get("observations", [])
        
        # 初始化RAG检索器
        try:
            knowledge_retriever = create_knowledge_retriever("historical")  # 使用历史数据检索器
        except Exception as e:
            logger.warning(f"Failed to initialize RAG retriever: {e}, falling back to rule-based approach")
            knowledge_retriever = None
        
        # 执行诊断
        if diag_step:
            # 获取日志数据和指标数据进行诊断
            log_data = {"logs": state.get("error_logs", [])}
            metrics_data = [metric.dict() for metric in state.get("training_metrics", [])]
            
            # 传统诊断
            diagnosis_result = diagnose_training_issues.invoke({
                "task_id": task_id,
                "log_data": log_data,
                "metrics_data": metrics_data
            })
            
            # RAG增强诊断
            rag_solutions = []
            if knowledge_retriever and diagnosis_result.get("issues_found"):
                for issue in diagnosis_result["issues_found"]:
                    if isinstance(issue, dict) and "message" in issue:
                        problem_desc = issue["message"]
                    else:
                        problem_desc = str(issue)
                    
                    try:
                        solutions = await knowledge_retriever.retrieve_solutions(problem_desc, top_k=2)
                        for solution in solutions:
                            rag_solutions.extend(solution.solutions_applied)
                    except Exception as e:
                        logger.warning(f"RAG solution retrieval failed: {e}")
            
            # 合并诊断结果
            if rag_solutions:
                diagnosis_result["rag_solutions"] = list(set(rag_solutions))  # 去重
                diagnosis_result["recommendations"].extend(rag_solutions)
                observations.append(f"Enhanced diagnosis with {len(rag_solutions)} RAG-retrieved solutions")
            
            diag_step.execution_res = json.dumps(diagnosis_result, ensure_ascii=False)
            observations.append(f"Completed issue diagnosis for task {task_id}")
        
        # 生成优化建议
        if opt_step:
            recommendations = []
            
            # 基于性能数据生成建议
            performance_data = state.get("performance_data", {})
            if "analysis" in performance_data:
                analysis = performance_data["analysis"]
                
                # 损失相关建议
                if "loss" in analysis:
                    loss_info = analysis["loss"]
                    if loss_info.get("trend") == "increasing":
                        recommendations.append("Learning rate may be too high, consider reducing it")
                    elif loss_info.get("improvement", 0) < 5:
                        recommendations.append("Loss improvement is minimal, consider adjusting hyperparameters")
                
                # 准确率相关建议
                if "accuracy" in analysis:
                    acc_info = analysis["accuracy"]
                    if acc_info.get("trend") == "decreasing":
                        recommendations.append("Accuracy is decreasing, check for overfitting")
            
            # 基于资源使用生成建议
            resource_usage = state.get("resource_usage", [])
            for resource in resource_usage:
                usage_ratio = resource.current_usage / resource.max_usage if resource.max_usage > 0 else 0
                if usage_ratio > 0.9:
                    recommendations.append(f"High {resource.resource_type.value} usage ({usage_ratio:.1%}), consider optimization")
                elif usage_ratio < 0.3:
                    recommendations.append(f"Low {resource.resource_type.value} usage ({usage_ratio:.1%}), resources may be underutilized")
            
            # RAG增强优化建议
            rag_tips = []
            if knowledge_retriever:
                try:
                    # 构建上下文
                    rag_context = {}
                    if performance_data and "analysis" in performance_data:
                        analysis = performance_data["analysis"]
                        if "loss" in analysis:
                            trend = analysis["loss"].get("trend")
                            if trend == "increasing":
                                rag_context["loss_trend"] = "diverging"
                            elif analysis["loss"].get("improvement", 0) < 5:
                                rag_context["loss_trend"] = "plateau"
                    
                    if resource_usage:
                        gpu_resources = [r for r in resource_usage if r.resource_type.value == "gpu"]
                        if gpu_resources:
                            gpu_usage = gpu_resources[0].current_usage / gpu_resources[0].max_usage
                            rag_context["resource_usage"] = {"gpu_usage": gpu_usage}
                    
                    rag_tips = await knowledge_retriever.retrieve_optimization_tips(rag_context, top_k=5)
                    recommendations.extend(rag_tips)
                    observations.append(f"Enhanced recommendations with {len(rag_tips)} RAG-retrieved tips")
                    
                except Exception as e:
                    logger.warning(f"RAG optimization tips retrieval failed: {e}")
            
            # 检索相似任务的经验
            similar_task_tips = []
            if knowledge_retriever:
                try:
                    training_task = state.get("training_task")
                    if training_task:
                        query_task = {
                            "model_name": training_task.model_name,
                            "task_type": "classification",  # 默认，实际应该从任务信息中提取
                            "dataset_name": training_task.dataset_name
                        }
                        
                        similar_tasks = await knowledge_retriever.retrieve_similar_tasks(query_task, top_k=3)
                        for task in similar_tasks:
                            similar_task_tips.extend(task.optimization_tips)
                        
                        if similar_task_tips:
                            recommendations.extend(similar_task_tips)
                            observations.append(f"Added {len(similar_task_tips)} tips from {len(similar_tasks)} similar tasks")
                            
                except Exception as e:
                    logger.warning(f"Similar task retrieval failed: {e}")
            
            # 去重优化建议
            unique_recommendations = list(dict.fromkeys(recommendations))
            
            opt_recommendations = {
                "task_id": task_id,
                "recommendations": unique_recommendations,
                "rag_enhanced": len(rag_tips) > 0 or len(similar_task_tips) > 0,
                "priority": "high" if len(state.get("error_logs", [])) > 0 else "medium"
            }
            
            opt_step.execution_res = json.dumps(opt_recommendations, ensure_ascii=False)
            observations.append(f"Generated {len(unique_recommendations)} optimization recommendations for task {task_id}")
        
        update_data = {
            "current_plan": plan,
            "observations": observations
        }
        
        return Command(goto="reporter", update=update_data)
        
    except Exception as e:
        logger.error(f"Error in diagnostics: {str(e)}")
        if diag_step:
            diag_step.execution_res = f"Error: {str(e)}"
        if opt_step:
            opt_step.execution_res = f"Error: {str(e)}"
        return Command(goto="reporter", update={"current_plan": plan})


def reporter_node(state: TrainingAgentState, config: RunnableConfig) -> Command[Literal["__end__"]]:
    """
    报告器节点 - 生成最终的深度研究报告
    """
    logger.info("Reporter node is running")
    
    task_id = state.get("task_id", "")
    plan = state.get("current_plan")
    training_task = state.get("training_task")
    
    # 生成综合报告
    report_sections = []
    
    # 1. 执行摘要
    report_sections.append("# Training Task Deep Research Report")
    report_sections.append(f"\n## Executive Summary")
    report_sections.append(f"**Task ID:** {task_id}")
    
    if training_task:
        report_sections.append(f"**Task Name:** {training_task.name}")
        report_sections.append(f"**Status:** {training_task.status.value}")
        report_sections.append(f"**Model:** {training_task.model_name or 'Unknown'}")
        report_sections.append(f"**Dataset:** {training_task.dataset_name or 'Unknown'}")
    
    # 2. 研究步骤执行结果
    if plan:
        report_sections.append(f"\n## Research Execution Results")
        for i, step in enumerate(plan.steps, 1):
            report_sections.append(f"\n### {i}. {step.title}")
            report_sections.append(f"**Type:** {step.step_type.value}")
            report_sections.append(f"**Description:** {step.description}")
            
            if step.execution_res:
                if step.execution_res.startswith("Error:"):
                    report_sections.append(f"**Status:** ❌ Failed")
                    report_sections.append(f"**Error:** {step.execution_res}")
                else:
                    report_sections.append(f"**Status:** ✅ Completed")
                    # 尝试解析和总结结果
                    try:
                        result_data = json.loads(step.execution_res)
                        if step.step_type == StepType.PERFORMANCE_ANALYSIS:
                            if "analysis" in result_data:
                                analysis = result_data["analysis"]["analysis"]
                                if "loss" in analysis:
                                    loss_info = analysis["loss"]
                                    report_sections.append(f"**Loss Analysis:** {loss_info.get('trend', 'unknown')} trend, {loss_info.get('improvement', 0):.2f}% improvement")
                                if "accuracy" in analysis:
                                    acc_info = analysis["accuracy"] 
                                    report_sections.append(f"**Accuracy Analysis:** {acc_info.get('trend', 'unknown')} trend, {acc_info.get('improvement', 0):.2f}% improvement")
                        elif step.step_type == StepType.OPTIMIZATION:
                            if "recommendations" in result_data:
                                recs = result_data["recommendations"]
                                report_sections.append(f"**Recommendations:** {len(recs)} optimization suggestions generated")
                    except:
                        report_sections.append(f"**Raw Result:** {step.execution_res[:200]}...")
            else:
                report_sections.append(f"**Status:** ⏳ Not executed")
    
    # 3. 关键发现
    report_sections.append(f"\n## Key Findings")
    
    observations = state.get("observations", [])
    if observations:
        for obs in observations:
            report_sections.append(f"- {obs}")
    else:
        report_sections.append("- No specific observations recorded")
    
    # 4. 性能总结
    performance_data = state.get("performance_data", {})
    if performance_data and "analysis" in performance_data:
        report_sections.append(f"\n## Performance Summary")
        analysis = performance_data["analysis"]
        
        if "loss" in analysis:
            loss_info = analysis["loss"]
            report_sections.append(f"**Loss Performance:**")
            report_sections.append(f"- Initial: {loss_info.get('initial', 'N/A')}")
            report_sections.append(f"- Final: {loss_info.get('final', 'N/A')}")
            report_sections.append(f"- Trend: {loss_info.get('trend', 'N/A')}")
            report_sections.append(f"- Improvement: {loss_info.get('improvement', 0):.2f}%")
        
        if "accuracy" in analysis:
            acc_info = analysis["accuracy"]
            report_sections.append(f"\n**Accuracy Performance:**")
            report_sections.append(f"- Initial: {acc_info.get('initial', 'N/A')}")
            report_sections.append(f"- Final: {acc_info.get('final', 'N/A')}")
            report_sections.append(f"- Trend: {acc_info.get('trend', 'N/A')}")
            report_sections.append(f"- Improvement: {acc_info.get('improvement', 0):.2f}%")
    
    # 5. 资源使用总结
    resource_usage = state.get("resource_usage", [])
    if resource_usage:
        report_sections.append(f"\n## Resource Usage Summary")
        for resource in resource_usage:
            usage_pct = (resource.current_usage / resource.max_usage * 100) if resource.max_usage > 0 else 0
            report_sections.append(f"- **{resource.resource_type.value.upper()}:** {resource.current_usage:.2f}/{resource.max_usage:.2f} {resource.unit} ({usage_pct:.1f}%)")
    
    # 6. 问题和建议
    error_logs = state.get("error_logs", [])
    if error_logs:
        report_sections.append(f"\n## Issues Identified")
        report_sections.append(f"- {len(error_logs)} error entries found in logs")
        if len(error_logs) <= 5:
            for error in error_logs[:5]:
                report_sections.append(f"  - {error[:100]}...")
        else:
            report_sections.append(f"  - Showing first 5 of {len(error_logs)} errors")
            for error in error_logs[:5]:
                report_sections.append(f"  - {error[:100]}...")
    
    # 7. 结论
    report_sections.append(f"\n## Conclusion")
    
    if training_task and training_task.status.value == "completed":
        report_sections.append("✅ Training task completed successfully.")
    elif training_task and training_task.status.value == "failed":
        report_sections.append("❌ Training task failed. Review error logs for details.")
    elif training_task and training_task.status.value == "running":
        report_sections.append("🔄 Training task is currently running.")
    else:
        report_sections.append("ℹ️ Training task status unclear.")
    
    final_report = "\n".join(report_sections)
    
    return Command(
        goto="__end__",
        update={
            "final_report": final_report,
            "messages": state["messages"] + [
                AIMessage(content=f"Deep research completed for training task {task_id}. Report generated with comprehensive analysis.")
            ]
        }
    )