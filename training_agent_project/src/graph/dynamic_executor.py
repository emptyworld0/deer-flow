# Copyright (c) 2025
# SPDX-License-Identifier: MIT

import json
import logging
from typing import Dict, Any, List, Optional, Callable
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

from .types import TrainingAgentState, StepType, TrainingResearchStep
from ..tools.cluster_tools import (
    get_training_task_info,
    get_training_metrics,
    get_resource_usage,
    get_training_logs,
    analyze_training_performance,
    diagnose_training_issues
)
from ..rag.knowledge_retriever import create_knowledge_retriever

logger = logging.getLogger(__name__)


class StepExecutor:
    """步骤执行器基类"""
    
    def __init__(self, step_type: StepType):
        self.step_type = step_type
    
    async def execute(self, state: TrainingAgentState, config: RunnableConfig, step: TrainingResearchStep) -> Dict[str, Any]:
        """执行步骤并返回更新的状态"""
        raise NotImplementedError


class TaskInfoExecutor(StepExecutor):
    """任务信息收集执行器"""
    
    def __init__(self):
        super().__init__(StepType.TASK_INFO)
    
    async def execute(self, state: TrainingAgentState, config: RunnableConfig, step: TrainingResearchStep) -> Dict[str, Any]:
        """执行任务信息收集"""
        logger.info(f"Executing step: {step.title}")
        
        task_id = state.get("task_id", "")
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
                step.execution_res = f"Failed to get task info: {task_info_result['error']}"
                return {"error": task_info_result['error']}
            
            # 解析任务信息
            from .types import TrainingTask, TrainingStatus
            training_task = TrainingTask(
                task_id=task_info_result.get("task_id", task_id),
                name=task_info_result.get("name", f"Task {task_id}"),
                status=TrainingStatus(task_info_result.get("status", "unknown")),
                model_name=task_info_result.get("model_name"),
                dataset_name=task_info_result.get("dataset_name"),
                description=task_info_result.get("description")
            )
            
            step.execution_res = json.dumps(task_info_result, ensure_ascii=False)
            
            return {
                "training_task": training_task,
                "cluster_info": {"api_url": cluster_config["cluster_api_url"]}
            }
            
        except Exception as e:
            error_msg = f"Error in task info collection: {str(e)}"
            logger.error(error_msg)
            step.execution_res = error_msg
            return {"error": error_msg}


class PerformanceAnalysisExecutor(StepExecutor):
    """性能分析执行器"""
    
    def __init__(self):
        super().__init__(StepType.PERFORMANCE_ANALYSIS)
    
    async def execute(self, state: TrainingAgentState, config: RunnableConfig, step: TrainingResearchStep) -> Dict[str, Any]:
        """执行性能分析"""
        logger.info(f"Executing step: {step.title}")
        
        task_id = state.get("task_id", "")
        cluster_config = {
            "cluster_api_url": config.get("configurable", {}).get("cluster_api_url", "http://localhost:8080"),
            "auth_token": config.get("configurable", {}).get("auth_token")
        }
        
        try:
            # 获取训练指标
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
                
                step.execution_res = json.dumps({
                    "metrics": metrics_result,
                    "analysis": analysis_result
                }, ensure_ascii=False)
                
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
                
                return {
                    "training_metrics": training_metrics,
                    "performance_data": analysis_result
                }
            else:
                error_msg = "Failed to retrieve training metrics"
                if metrics_result and "error" in str(metrics_result):
                    error_msg = f"Metrics error: {metrics_result}"
                step.execution_res = error_msg
                return {"error": error_msg}
                
        except Exception as e:
            error_msg = f"Error in performance analysis: {str(e)}"
            logger.error(error_msg)
            step.execution_res = error_msg
            return {"error": error_msg}


class ResourceAnalysisExecutor(StepExecutor):
    """资源分析执行器"""
    
    def __init__(self):
        super().__init__(StepType.RESOURCE_ANALYSIS)
    
    async def execute(self, state: TrainingAgentState, config: RunnableConfig, step: TrainingResearchStep) -> Dict[str, Any]:
        """执行资源分析"""
        logger.info(f"Executing step: {step.title}")
        
        task_id = state.get("task_id", "")
        cluster_config = {
            "cluster_api_url": config.get("configurable", {}).get("cluster_api_url", "http://localhost:8080"),
            "auth_token": config.get("configurable", {}).get("auth_token")
        }
        
        try:
            # 获取资源使用数据
            resource_result = get_resource_usage.invoke({
                "task_id": task_id,
                "cluster_config": cluster_config
            })
            
            if isinstance(resource_result, list) and len(resource_result) > 0 and "error" not in resource_result[0]:
                step.execution_res = json.dumps(resource_result, ensure_ascii=False)
                
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
                
                return {"resource_usage": resource_usage}
            else:
                error_msg = "Failed to retrieve resource usage data"
                if resource_result and "error" in str(resource_result):
                    error_msg = f"Resource error: {resource_result}"
                step.execution_res = error_msg
                return {"error": error_msg}
                
        except Exception as e:
            error_msg = f"Error in resource analysis: {str(e)}"
            logger.error(error_msg)
            step.execution_res = error_msg
            return {"error": error_msg}


class LogAnalysisExecutor(StepExecutor):
    """日志分析执行器"""
    
    def __init__(self):
        super().__init__(StepType.LOG_ANALYSIS)
    
    async def execute(self, state: TrainingAgentState, config: RunnableConfig, step: TrainingResearchStep) -> Dict[str, Any]:
        """执行日志分析"""
        logger.info(f"Executing step: {step.title}")
        
        task_id = state.get("task_id", "")
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
            
            step.execution_res = json.dumps(all_logs, ensure_ascii=False)
            
            # 提取错误日志
            error_logs = []
            if "error" in all_logs and isinstance(all_logs["error"], list):
                error_logs = [log.get("message", "") for log in all_logs["error"]]
            
            return {"error_logs": error_logs}
            
        except Exception as e:
            error_msg = f"Error in log analysis: {str(e)}"
            logger.error(error_msg)
            step.execution_res = error_msg
            return {"error": error_msg}


class ErrorDiagnosisExecutor(StepExecutor):
    """错误诊断执行器"""
    
    def __init__(self):
        super().__init__(StepType.ERROR_DIAGNOSIS)
    
    async def execute(self, state: TrainingAgentState, config: RunnableConfig, step: TrainingResearchStep) -> Dict[str, Any]:
        """执行错误诊断"""
        logger.info(f"Executing step: {step.title}")
        
        task_id = state.get("task_id", "")
        
        try:
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
            try:
                knowledge_retriever = create_knowledge_retriever("historical")
                rag_solutions = []
                
                if diagnosis_result.get("issues_found"):
                    for issue in diagnosis_result["issues_found"]:
                        if isinstance(issue, dict) and "message" in issue:
                            problem_desc = issue["message"]
                        else:
                            problem_desc = str(issue)
                        
                        solutions = await knowledge_retriever.retrieve_solutions(problem_desc, top_k=2)
                        for solution in solutions:
                            rag_solutions.extend(solution.solutions_applied)
                
                if rag_solutions:
                    diagnosis_result["rag_solutions"] = list(set(rag_solutions))
                    diagnosis_result["recommendations"].extend(rag_solutions)
                    
            except Exception as e:
                logger.warning(f"RAG enhancement failed: {e}")
            
            step.execution_res = json.dumps(diagnosis_result, ensure_ascii=False)
            return {"diagnosis_result": diagnosis_result}
            
        except Exception as e:
            error_msg = f"Error in error diagnosis: {str(e)}"
            logger.error(error_msg)
            step.execution_res = error_msg
            return {"error": error_msg}


class OptimizationExecutor(StepExecutor):
    """优化建议执行器"""
    
    def __init__(self):
        super().__init__(StepType.OPTIMIZATION)
    
    async def execute(self, state: TrainingAgentState, config: RunnableConfig, step: TrainingResearchStep) -> Dict[str, Any]:
        """执行优化建议生成"""
        logger.info(f"Executing step: {step.title}")
        
        task_id = state.get("task_id", "")
        
        try:
            recommendations = []
            
            # 基于性能数据生成建议
            performance_data = state.get("performance_data", {})
            if "analysis" in performance_data:
                analysis = performance_data["analysis"]
                
                if "loss" in analysis:
                    loss_info = analysis["loss"]
                    if loss_info.get("trend") == "increasing":
                        recommendations.append("Learning rate may be too high, consider reducing it")
                    elif loss_info.get("improvement", 0) < 5:
                        recommendations.append("Loss improvement is minimal, consider adjusting hyperparameters")
                
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
            try:
                knowledge_retriever = create_knowledge_retriever("historical")
                
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
                
                # 检索相似任务的经验
                training_task = state.get("training_task")
                if training_task:
                    query_task = {
                        "model_name": training_task.model_name,
                        "task_type": "classification",
                        "dataset_name": training_task.dataset_name
                    }
                    
                    similar_tasks = await knowledge_retriever.retrieve_similar_tasks(query_task, top_k=3)
                    for task in similar_tasks:
                        recommendations.extend(task.optimization_tips)
                        
            except Exception as e:
                logger.warning(f"RAG optimization enhancement failed: {e}")
            
            # 去重优化建议
            unique_recommendations = list(dict.fromkeys(recommendations))
            
            opt_recommendations = {
                "task_id": task_id,
                "recommendations": unique_recommendations,
                "priority": "high" if len(state.get("error_logs", [])) > 0 else "medium"
            }
            
            step.execution_res = json.dumps(opt_recommendations, ensure_ascii=False)
            return {"optimization_recommendations": opt_recommendations}
            
        except Exception as e:
            error_msg = f"Error in optimization: {str(e)}"
            logger.error(error_msg)
            step.execution_res = error_msg
            return {"error": error_msg}


class ComparisonExecutor(StepExecutor):
    """对比分析执行器"""
    
    def __init__(self):
        super().__init__(StepType.COMPARISON)
    
    async def execute(self, state: TrainingAgentState, config: RunnableConfig, step: TrainingResearchStep) -> Dict[str, Any]:
        """执行对比分析"""
        logger.info(f"Executing step: {step.title}")
        
        # 这里可以实现与其他任务的对比分析逻辑
        # 暂时返回基本信息
        comparison_result = {
            "message": "Comparison analysis not yet implemented",
            "task_id": state.get("task_id", "")
        }
        
        step.execution_res = json.dumps(comparison_result, ensure_ascii=False)
        return {"comparison_result": comparison_result}


class DynamicStepExecutor:
    """动态步骤执行器管理器"""
    
    def __init__(self):
        self.executors: Dict[StepType, StepExecutor] = {
            StepType.TASK_INFO: TaskInfoExecutor(),
            StepType.PERFORMANCE_ANALYSIS: PerformanceAnalysisExecutor(),
            StepType.RESOURCE_ANALYSIS: ResourceAnalysisExecutor(),
            StepType.LOG_ANALYSIS: LogAnalysisExecutor(),
            StepType.ERROR_DIAGNOSIS: ErrorDiagnosisExecutor(),
            StepType.OPTIMIZATION: OptimizationExecutor(),
            StepType.COMPARISON: ComparisonExecutor(),
        }
    
    async def execute_step(self, state: TrainingAgentState, config: RunnableConfig, step: TrainingResearchStep) -> Dict[str, Any]:
        """执行单个步骤"""
        executor = self.executors.get(step.step_type)
        if not executor:
            error_msg = f"No executor found for step type: {step.step_type}"
            logger.error(error_msg)
            step.execution_res = error_msg
            return {"error": error_msg}
        
        return await executor.execute(state, config, step)
    
    def get_next_step(self, plan) -> Optional[TrainingResearchStep]:
        """获取下一个需要执行的步骤"""
        if not plan or not plan.steps:
            return None
        
        for step in plan.steps:
            if not step.execution_res:  # 找到第一个未执行的步骤
                return step
        
        return None  # 所有步骤都已执行


# 全局执行器实例
dynamic_executor = DynamicStepExecutor()