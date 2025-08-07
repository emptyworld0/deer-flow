# Copyright (c) 2025
# SPDX-License-Identifier: MIT

import json
import logging
import subprocess
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from ..graph.types import TrainingTask, TrainingMetrics, ResourceUsage, TrainingStatus

logger = logging.getLogger(__name__)


class ClusterConfig(BaseModel):
    """集群配置"""
    cluster_api_url: str = Field(..., description="集群API地址")
    auth_token: Optional[str] = Field(None, description="认证token")
    timeout: int = Field(default=30, description="请求超时时间")


@tool
def get_training_task_info(
    task_id: str,
    cluster_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    从训练集群获取指定任务的基本信息
    
    Args:
        task_id: 训练任务ID
        cluster_config: 集群配置信息
        
    Returns:
        训练任务的详细信息
    """
    try:
        config = ClusterConfig(**cluster_config)
        headers = {}
        if config.auth_token:
            headers["Authorization"] = f"Bearer {config.auth_token}"
            
        response = requests.get(
            f"{config.cluster_api_url}/api/v1/training/tasks/{task_id}",
            headers=headers,
            timeout=config.timeout
        )
        response.raise_for_status()
        
        task_data = response.json()
        logger.info(f"Successfully retrieved task info for {task_id}")
        return task_data
        
    except Exception as e:
        logger.error(f"Failed to get task info for {task_id}: {str(e)}")
        return {"error": str(e), "task_id": task_id}


@tool
def get_training_metrics(
    task_id: str,
    cluster_config: Dict[str, Any],
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    获取训练任务的性能指标数据
    
    Args:
        task_id: 训练任务ID
        cluster_config: 集群配置信息
        start_time: 开始时间 (ISO格式)
        end_time: 结束时间 (ISO格式)
        
    Returns:
        训练指标数据列表
    """
    try:
        config = ClusterConfig(**cluster_config)
        headers = {}
        if config.auth_token:
            headers["Authorization"] = f"Bearer {config.auth_token}"
            
        params = {}
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time
            
        response = requests.get(
            f"{config.cluster_api_url}/api/v1/training/tasks/{task_id}/metrics",
            headers=headers,
            params=params,
            timeout=config.timeout
        )
        response.raise_for_status()
        
        metrics_data = response.json()
        logger.info(f"Successfully retrieved metrics for {task_id}")
        return metrics_data.get("metrics", [])
        
    except Exception as e:
        logger.error(f"Failed to get metrics for {task_id}: {str(e)}")
        return [{"error": str(e), "task_id": task_id}]


@tool
def get_resource_usage(
    task_id: str,
    cluster_config: Dict[str, Any],
    resource_types: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    获取训练任务的资源使用情况
    
    Args:
        task_id: 训练任务ID
        cluster_config: 集群配置信息
        resource_types: 资源类型列表 (gpu, cpu, memory, storage)
        
    Returns:
        资源使用数据列表
    """
    try:
        config = ClusterConfig(**cluster_config)
        headers = {}
        if config.auth_token:
            headers["Authorization"] = f"Bearer {config.auth_token}"
            
        params = {}
        if resource_types:
            params["resource_types"] = ",".join(resource_types)
            
        response = requests.get(
            f"{config.cluster_api_url}/api/v1/training/tasks/{task_id}/resources",
            headers=headers,
            params=params,
            timeout=config.timeout
        )
        response.raise_for_status()
        
        resource_data = response.json()
        logger.info(f"Successfully retrieved resource usage for {task_id}")
        return resource_data.get("resources", [])
        
    except Exception as e:
        logger.error(f"Failed to get resource usage for {task_id}: {str(e)}")
        return [{"error": str(e), "task_id": task_id}]


@tool
def get_training_logs(
    task_id: str,
    cluster_config: Dict[str, Any],
    log_type: str = "training",
    max_lines: int = 1000,
    since: Optional[str] = None
) -> Dict[str, Any]:
    """
    获取训练任务的日志
    
    Args:
        task_id: 训练任务ID
        cluster_config: 集群配置信息
        log_type: 日志类型 (training, error, system)
        max_lines: 最大行数
        since: 从什么时间开始 (ISO格式)
        
    Returns:
        日志数据
    """
    try:
        config = ClusterConfig(**cluster_config)
        headers = {}
        if config.auth_token:
            headers["Authorization"] = f"Bearer {config.auth_token}"
            
        params = {
            "log_type": log_type,
            "max_lines": max_lines
        }
        if since:
            params["since"] = since
            
        response = requests.get(
            f"{config.cluster_api_url}/api/v1/training/tasks/{task_id}/logs",
            headers=headers,
            params=params,
            timeout=config.timeout
        )
        response.raise_for_status()
        
        log_data = response.json()
        logger.info(f"Successfully retrieved {log_type} logs for {task_id}")
        return log_data
        
    except Exception as e:
        logger.error(f"Failed to get logs for {task_id}: {str(e)}")
        return {"error": str(e), "task_id": task_id, "logs": []}


@tool
def analyze_training_performance(
    task_id: str,
    metrics_data: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    分析训练性能数据
    
    Args:
        task_id: 训练任务ID
        metrics_data: 训练指标数据
        
    Returns:
        性能分析结果
    """
    try:
        if not metrics_data:
            return {"error": "No metrics data provided", "task_id": task_id}
            
        analysis = {
            "task_id": task_id,
            "total_metrics": len(metrics_data),
            "analysis": {}
        }
        
        # 提取关键指标
        losses = [m.get("loss") for m in metrics_data if m.get("loss") is not None]
        accuracies = [m.get("accuracy") for m in metrics_data if m.get("accuracy") is not None]
        learning_rates = [m.get("learning_rate") for m in metrics_data if m.get("learning_rate") is not None]
        
        # 损失分析
        if losses:
            analysis["analysis"]["loss"] = {
                "initial": losses[0],
                "final": losses[-1],
                "min": min(losses),
                "max": max(losses),
                "trend": "decreasing" if losses[-1] < losses[0] else "increasing",
                "improvement": (losses[0] - losses[-1]) / losses[0] * 100 if losses[0] != 0 else 0
            }
            
        # 准确率分析
        if accuracies:
            analysis["analysis"]["accuracy"] = {
                "initial": accuracies[0],
                "final": accuracies[-1],
                "min": min(accuracies),
                "max": max(accuracies),
                "trend": "increasing" if accuracies[-1] > accuracies[0] else "decreasing",
                "improvement": (accuracies[-1] - accuracies[0]) / accuracies[0] * 100 if accuracies[0] != 0 else 0
            }
            
        # 学习率分析
        if learning_rates:
            analysis["analysis"]["learning_rate"] = {
                "initial": learning_rates[0],
                "final": learning_rates[-1],
                "min": min(learning_rates),
                "max": max(learning_rates),
                "decay_pattern": "exponential" if learning_rates[-1] < learning_rates[0] * 0.5 else "linear"
            }
            
        logger.info(f"Successfully analyzed performance for {task_id}")
        return analysis
        
    except Exception as e:
        logger.error(f"Failed to analyze performance for {task_id}: {str(e)}")
        return {"error": str(e), "task_id": task_id}


@tool
def diagnose_training_issues(
    task_id: str,
    log_data: Dict[str, Any],
    metrics_data: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    诊断训练任务中的问题
    
    Args:
        task_id: 训练任务ID
        log_data: 日志数据
        metrics_data: 指标数据
        
    Returns:
        问题诊断结果
    """
    try:
        diagnosis = {
            "task_id": task_id,
            "issues_found": [],
            "recommendations": []
        }
        
        logs = log_data.get("logs", [])
        
        # 检查错误日志
        error_keywords = ["error", "exception", "failed", "timeout", "out of memory", "cuda error"]
        for log_entry in logs:
            log_content = log_entry.get("message", "").lower()
            for keyword in error_keywords:
                if keyword in log_content:
                    diagnosis["issues_found"].append({
                        "type": "error",
                        "keyword": keyword,
                        "message": log_entry.get("message", ""),
                        "timestamp": log_entry.get("timestamp")
                    })
                    
        # 检查性能问题
        if metrics_data:
            losses = [m.get("loss") for m in metrics_data if m.get("loss") is not None]
            if len(losses) > 10:
                # 检查损失是否停滞
                recent_losses = losses[-10:]
                if max(recent_losses) - min(recent_losses) < 0.001:
                    diagnosis["issues_found"].append({
                        "type": "performance",
                        "issue": "loss_plateau",
                        "description": "Loss has plateaued in recent iterations"
                    })
                    diagnosis["recommendations"].append("Consider adjusting learning rate or optimizer")
                    
                # 检查损失是否发散
                if len(losses) > 1 and losses[-1] > losses[0] * 2:
                    diagnosis["issues_found"].append({
                        "type": "performance",
                        "issue": "loss_divergence",
                        "description": "Loss appears to be diverging"
                    })
                    diagnosis["recommendations"].append("Consider reducing learning rate")
                    
        # 检查资源使用问题
        if "out of memory" in str(logs).lower():
            diagnosis["recommendations"].append("Consider reducing batch size or model size")
            
        logger.info(f"Successfully diagnosed issues for {task_id}")
        return diagnosis
        
    except Exception as e:
        logger.error(f"Failed to diagnose issues for {task_id}: {str(e)}")
        return {"error": str(e), "task_id": task_id}


@tool  
def compare_training_tasks(
    task_ids: List[str],
    cluster_config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    比较多个训练任务的性能
    
    Args:
        task_ids: 训练任务ID列表
        cluster_config: 集群配置信息
        
    Returns:
        任务比较结果
    """
    try:
        comparison = {
            "task_count": len(task_ids),
            "tasks": {},
            "comparison_summary": {}
        }
        
        # 获取每个任务的信息
        for task_id in task_ids:
            task_info = get_training_task_info(task_id, cluster_config)
            metrics = get_training_metrics(task_id, cluster_config)
            
            if "error" not in task_info:
                comparison["tasks"][task_id] = {
                    "info": task_info,
                    "metrics_count": len(metrics),
                    "final_metrics": metrics[-1] if metrics else None
                }
                
        # 生成比较摘要
        if len(comparison["tasks"]) > 1:
            task_data = list(comparison["tasks"].values())
            
            # 比较最终指标
            final_losses = []
            final_accuracies = []
            
            for task in task_data:
                final_metric = task.get("final_metrics")
                if final_metric:
                    if final_metric.get("loss"):
                        final_losses.append(final_metric["loss"])
                    if final_metric.get("accuracy"):
                        final_accuracies.append(final_metric["accuracy"])
                        
            if final_losses:
                best_loss_idx = final_losses.index(min(final_losses))
                comparison["comparison_summary"]["best_loss"] = {
                    "task_id": task_ids[best_loss_idx],
                    "value": min(final_losses)
                }
                
            if final_accuracies:
                best_acc_idx = final_accuracies.index(max(final_accuracies))
                comparison["comparison_summary"]["best_accuracy"] = {
                    "task_id": task_ids[best_acc_idx], 
                    "value": max(final_accuracies)
                }
                
        logger.info(f"Successfully compared {len(task_ids)} training tasks")
        return comparison
        
    except Exception as e:
        logger.error(f"Failed to compare training tasks: {str(e)}")
        return {"error": str(e), "task_ids": task_ids}