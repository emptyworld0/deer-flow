# Copyright (c) 2025
# SPDX-License-Identifier: MIT

from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from langgraph.graph import MessagesState
from pydantic import BaseModel, Field


class TrainingStatus(str, Enum):
    """训练任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class ResourceType(str, Enum):
    """资源类型枚举"""
    GPU = "gpu"
    CPU = "cpu"
    MEMORY = "memory"
    STORAGE = "storage"
    NETWORK = "network"


class TrainingMetrics(BaseModel):
    """训练指标数据模型"""
    loss: Optional[float] = None
    accuracy: Optional[float] = None
    learning_rate: Optional[float] = None
    epoch: Optional[int] = None
    step: Optional[int] = None
    timestamp: Optional[datetime] = None
    custom_metrics: Dict[str, Any] = Field(default_factory=dict)


class ResourceUsage(BaseModel):
    """资源使用情况数据模型"""
    resource_type: ResourceType
    current_usage: float
    max_usage: float
    unit: str
    timestamp: Optional[datetime] = None


class TrainingTask(BaseModel):
    """训练任务基本信息"""
    task_id: str
    name: str
    status: TrainingStatus
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    model_name: Optional[str] = None
    dataset_name: Optional[str] = None
    config_path: Optional[str] = None
    log_path: Optional[str] = None
    checkpoint_path: Optional[str] = None
    user_id: Optional[str] = None
    description: Optional[str] = None


class TrainingPlan(BaseModel):
    """训练任务研究计划"""
    locale: str = Field(default="en-US", description="语言区域")
    has_enough_context: bool = False
    thought: str = ""
    title: str = ""
    steps: List["TrainingResearchStep"] = Field(default_factory=list)


class StepType(str, Enum):
    """研究步骤类型"""
    TASK_INFO = "task_info"           # 获取任务基本信息
    RESOURCE_ANALYSIS = "resource"    # 资源使用分析
    PERFORMANCE_ANALYSIS = "performance"  # 性能分析
    LOG_ANALYSIS = "log_analysis"     # 日志分析
    ERROR_DIAGNOSIS = "error_diagnosis"  # 错误诊断
    COMPARISON = "comparison"         # 对比分析
    OPTIMIZATION = "optimization"     # 优化建议


class TrainingResearchStep(BaseModel):
    """训练任务研究步骤"""
    need_cluster_access: bool = Field(..., description="是否需要访问集群系统")
    title: str
    description: str = Field(..., description="具体要收集的数据")
    step_type: StepType = Field(..., description="步骤类型")
    execution_res: Optional[str] = Field(default=None, description="执行结果")


class TrainingAgentState(MessagesState):
    """训练任务研究Agent的状态管理"""
    
    # 核心任务信息
    task_id: str = ""
    training_task: Optional[TrainingTask] = None
    
    # 研究相关
    research_topic: str = ""
    observations: List[str] = Field(default_factory=list)
    plan_iterations: int = 0
    current_plan: Optional[TrainingPlan] = None
    final_report: str = ""
    auto_accepted_plan: bool = False
    
    # 训练任务特定数据
    training_metrics: List[TrainingMetrics] = Field(default_factory=list)
    resource_usage: List[ResourceUsage] = Field(default_factory=list)
    error_logs: List[str] = Field(default_factory=list)
    performance_data: Dict[str, Any] = Field(default_factory=dict)
    cluster_info: Dict[str, Any] = Field(default_factory=dict)
    
    # 配置和元数据
    locale: str = "en-US"
    enable_detailed_analysis: bool = True
    max_log_lines: int = 1000
    analysis_depth: str = "detailed"  # basic, detailed, comprehensive