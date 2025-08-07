# Copyright (c) 2025
# SPDX-License-Identifier: MIT

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import json

from ..graph.builder import build_graph, build_graph_with_memory
from ..graph.types import TrainingAgentState

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="Training Task Deep Research API",
    description="深度研究训练任务的AI Agent API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 请求/响应模型
class TrainingResearchRequest(BaseModel):
    """训练任务研究请求"""
    task_id: str = Field(..., description="训练任务ID")
    analysis_depth: str = Field(default="detailed", description="分析深度: basic, detailed, comprehensive")
    max_log_lines: int = Field(default=1000, description="最大日志行数")
    cluster_config: Optional[Dict[str, Any]] = Field(default=None, description="集群配置信息")
    enable_streaming: bool = Field(default=True, description="是否启用流式响应")


class TrainingResearchResponse(BaseModel):
    """训练任务研究响应"""
    task_id: str
    status: str
    report: Optional[str] = None
    error: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    execution_time: Optional[float] = None


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str
    status: str
    progress: float
    current_step: Optional[str] = None
    message: Optional[str] = None


# 全局状态存储 (实际生产环境应使用数据库)
research_tasks: Dict[str, Dict[str, Any]] = {}


# 依赖注入
def get_cluster_config() -> Dict[str, Any]:
    """获取默认集群配置"""
    return {
        "cluster_api_url": "http://localhost:8080",
        "auth_token": None,
        "timeout": 30
    }


async def stream_research_progress(task_id: str, request: TrainingResearchRequest):
    """
    流式执行训练任务研究
    """
    try:
        # 初始化任务状态
        research_tasks[task_id] = {
            "status": "running",
            "started_at": datetime.now(),
            "progress": 0.0,
            "current_step": "initializing"
        }
        
        # 构建工作流
        workflow = build_graph()
        
        # 准备初始状态
        cluster_config = request.cluster_config or get_cluster_config()
        initial_state = {
            "messages": [{"role": "user", "content": request.task_id}],
            "task_id": request.task_id,
            "analysis_depth": request.analysis_depth,
            "max_log_lines": request.max_log_lines,
            "locale": "zh-CN"
        }
        
        # 配置
        config = {
            "configurable": {
                "thread_id": f"research_{task_id}",
                "cluster_api_url": cluster_config.get("cluster_api_url"),
                "auth_token": cluster_config.get("auth_token"),
                "timeout": cluster_config.get("timeout", 30)
            },
            "recursion_limit": 50
        }
        
        step_count = 0
        total_steps = 7  # coordinator, planner, task_analyzer, performance_analyzer, log_analyzer, diagnostics, reporter
        
        # 执行工作流
        async for state in workflow.astream(
            input=initial_state,
            config=config,
            stream_mode="values"
        ):
            step_count += 1
            progress = min(step_count / total_steps, 1.0)
            
            # 更新任务状态
            research_tasks[task_id]["progress"] = progress
            
            # 从状态中提取当前步骤信息
            current_step = "processing"
            message = ""
            
            if isinstance(state, dict):
                if "messages" in state and state["messages"]:
                    latest_message = state["messages"][-1]
                    if isinstance(latest_message, dict):
                        message = latest_message.get("content", "")
                
                observations = state.get("observations", [])
                if observations:
                    current_step = f"Step {len(observations)}: {observations[-1]}"
                
                research_tasks[task_id]["current_step"] = current_step
                research_tasks[task_id]["message"] = message
            
            # 流式输出进度
            if request.enable_streaming:
                progress_data = {
                    "task_id": task_id,
                    "progress": progress,
                    "current_step": current_step,
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                }
                yield f"data: {json.dumps(progress_data)}\n\n"
        
        # 获取最终状态
        final_state = state
        final_report = final_state.get("final_report", "研究报告生成失败")
        
        # 更新任务完成状态
        completed_at = datetime.now()
        execution_time = (completed_at - research_tasks[task_id]["started_at"]).total_seconds()
        
        research_tasks[task_id].update({
            "status": "completed",
            "completed_at": completed_at,
            "execution_time": execution_time,
            "report": final_report,
            "progress": 1.0
        })
        
        # 发送完成信号
        if request.enable_streaming:
            completion_data = {
                "task_id": task_id,
                "status": "completed",
                "progress": 1.0,
                "report": final_report,
                "execution_time": execution_time,
                "timestamp": completed_at.isoformat()
            }
            yield f"data: {json.dumps(completion_data)}\n\n"
            yield "data: [DONE]\n\n"
        
    except Exception as e:
        logger.error(f"Error in research task {task_id}: {str(e)}")
        
        # 更新错误状态
        completed_at = datetime.now()
        execution_time = (completed_at - research_tasks[task_id]["started_at"]).total_seconds()
        
        research_tasks[task_id].update({
            "status": "failed",
            "completed_at": completed_at,
            "execution_time": execution_time,
            "error": str(e),
            "progress": 0.0
        })
        
        if request.enable_streaming:
            error_data = {
                "task_id": task_id,
                "status": "failed",
                "error": str(e),
                "timestamp": completed_at.isoformat()
            }
            yield f"data: {json.dumps(error_data)}\n\n"
            yield "data: [DONE]\n\n"


@app.post("/api/research/start", response_model=Dict[str, str])
async def start_research(request: TrainingResearchRequest, background_tasks: BackgroundTasks):
    """
    启动训练任务深度研究 (异步)
    """
    task_id = request.task_id
    
    # 检查任务是否已存在
    if task_id in research_tasks and research_tasks[task_id]["status"] == "running":
        raise HTTPException(status_code=400, detail=f"Research for task {task_id} is already running")
    
    # 启动后台任务
    background_tasks.add_task(
        lambda: asyncio.create_task(list(stream_research_progress(task_id, request)))
    )
    
    return {
        "task_id": task_id,
        "status": "started",
        "message": f"Deep research started for training task {task_id}"
    }


@app.post("/api/research/stream")
async def stream_research(request: TrainingResearchRequest):
    """
    启动训练任务深度研究 (流式)
    """
    task_id = request.task_id
    
    # 检查任务是否已存在
    if task_id in research_tasks and research_tasks[task_id]["status"] == "running":
        raise HTTPException(status_code=400, detail=f"Research for task {task_id} is already running")
    
    return StreamingResponse(
        stream_research_progress(task_id, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.get("/api/research/status/{task_id}", response_model=TaskStatusResponse)
async def get_research_status(task_id: str):
    """
    获取研究任务状态
    """
    if task_id not in research_tasks:
        raise HTTPException(status_code=404, detail=f"Research task {task_id} not found")
    
    task_data = research_tasks[task_id]
    return TaskStatusResponse(
        task_id=task_id,
        status=task_data["status"],
        progress=task_data.get("progress", 0.0),
        current_step=task_data.get("current_step"),
        message=task_data.get("message")
    )


@app.get("/api/research/report/{task_id}", response_model=TrainingResearchResponse)
async def get_research_report(task_id: str):
    """
    获取研究报告
    """
    if task_id not in research_tasks:
        raise HTTPException(status_code=404, detail=f"Research task {task_id} not found")
    
    task_data = research_tasks[task_id]
    
    return TrainingResearchResponse(
        task_id=task_id,
        status=task_data["status"],
        report=task_data.get("report"),
        error=task_data.get("error"),
        started_at=task_data["started_at"],
        completed_at=task_data.get("completed_at"),
        execution_time=task_data.get("execution_time")
    )


@app.delete("/api/research/{task_id}")
async def delete_research_task(task_id: str):
    """
    删除研究任务
    """
    if task_id not in research_tasks:
        raise HTTPException(status_code=404, detail=f"Research task {task_id} not found")
    
    del research_tasks[task_id]
    return {"message": f"Research task {task_id} deleted successfully"}


@app.get("/api/research/list")
async def list_research_tasks():
    """
    列出所有研究任务
    """
    task_list = []
    for task_id, data in research_tasks.items():
        task_list.append({
            "task_id": task_id,
            "status": data["status"],
            "started_at": data["started_at"].isoformat(),
            "progress": data.get("progress", 0.0)
        })
    
    return {"tasks": task_list, "total": len(task_list)}


@app.get("/api/health")
async def health_check():
    """
    健康检查接口
    """
    return {
        "status": "healthy",
        "service": "Training Task Deep Research API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/")
async def root():
    """
    根路径
    """
    return {
        "message": "Training Task Deep Research API",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "health_url": "/api/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )