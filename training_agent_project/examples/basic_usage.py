#!/usr/bin/env python3
"""
Training Task Deep Research Agent - 基本使用示例

本示例展示如何使用训练任务深度研究Agent来分析训练任务。
"""

import asyncio
import json
import time
from typing import Dict, Any

import aiohttp
import requests


class TrainingAgentClient:
    """训练任务研究Agent客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
    
    def start_research_async(self, task_id: str, **kwargs) -> Dict[str, Any]:
        """启动异步研究任务"""
        url = f"{self.base_url}/api/research/start"
        payload = {
            "task_id": task_id,
            "analysis_depth": kwargs.get("analysis_depth", "detailed"),
            "max_log_lines": kwargs.get("max_log_lines", 1000),
            "cluster_config": kwargs.get("cluster_config")
        }
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def get_research_status(self, task_id: str) -> Dict[str, Any]:
        """获取研究任务状态"""
        url = f"{self.base_url}/api/research/status/{task_id}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    
    def get_research_report(self, task_id: str) -> Dict[str, Any]:
        """获取研究报告"""
        url = f"{self.base_url}/api/research/report/{task_id}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    
    async def stream_research(self, task_id: str, **kwargs) -> None:
        """流式执行研究任务"""
        url = f"{self.base_url}/api/research/stream"
        payload = {
            "task_id": task_id,
            "analysis_depth": kwargs.get("analysis_depth", "detailed"),
            "max_log_lines": kwargs.get("max_log_lines", 1000),
            "cluster_config": kwargs.get("cluster_config"),
            "enable_streaming": True
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                response.raise_for_status()
                
                async for line in response.content:
                    line_str = line.decode('utf-8').strip()
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]  # 移除 'data: ' 前缀
                        if data_str == '[DONE]':
                            print("✅ 研究完成!")
                            break
                        
                        try:
                            data = json.loads(data_str)
                            self._handle_stream_data(data)
                        except json.JSONDecodeError:
                            continue
    
    def _handle_stream_data(self, data: Dict[str, Any]) -> None:
        """处理流式数据"""
        task_id = data.get("task_id", "unknown")
        progress = data.get("progress", 0)
        current_step = data.get("current_step", "")
        status = data.get("status", "running")
        
        if status == "completed":
            print(f"\n🎉 任务 {task_id} 研究完成!")
            if "report" in data:
                print("📋 研究报告已生成")
        elif status == "failed":
            error = data.get("error", "未知错误")
            print(f"\n❌ 任务 {task_id} 研究失败: {error}")
        else:
            progress_bar = "█" * int(progress * 20) + "░" * (20 - int(progress * 20))
            print(f"\r🔍 [{progress_bar}] {progress:.1%} - {current_step}", end="", flush=True)


def example_sync_usage():
    """同步使用示例"""
    print("🚀 训练任务深度研究 - 同步使用示例")
    print("=" * 50)
    
    # 创建客户端
    client = TrainingAgentClient()
    
    # 任务ID (替换为您的实际任务ID)
    task_id = "train-20241201-001"
    
    # 集群配置 (替换为您的实际配置)
    cluster_config = {
        "cluster_api_url": "http://localhost:8080",
        "auth_token": None,  # 或您的实际token
        "timeout": 30
    }
    
    try:
        # 1. 启动研究任务
        print(f"📋 启动任务 {task_id} 的深度研究...")
        result = client.start_research_async(
            task_id=task_id,
            analysis_depth="detailed",
            cluster_config=cluster_config
        )
        print(f"✅ 研究任务已启动: {result['message']}")
        
        # 2. 轮询任务状态
        print("\n🔍 监控研究进度...")
        while True:
            status = client.get_research_status(task_id)
            progress = status.get("progress", 0)
            current_step = status.get("current_step", "")
            task_status = status.get("status", "unknown")
            
            progress_bar = "█" * int(progress * 30) + "░" * (30 - int(progress * 30))
            print(f"\r[{progress_bar}] {progress:.1%} - {current_step}", end="", flush=True)
            
            if task_status == "completed":
                print("\n✅ 研究完成!")
                break
            elif task_status == "failed":
                print(f"\n❌ 研究失败!")
                break
            
            time.sleep(2)  # 等待2秒后再次检查
        
        # 3. 获取研究报告
        print("\n📋 获取研究报告...")
        report_data = client.get_research_report(task_id)
        
        if report_data.get("report"):
            print("\n" + "=" * 80)
            print("📊 研究报告:")
            print("=" * 80)
            print(report_data["report"])
            print("=" * 80)
            
            # 保存报告到文件
            filename = f"research_report_{task_id}.md"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(report_data["report"])
            print(f"💾 报告已保存到文件: {filename}")
        else:
            print("⚠️ 未找到研究报告")
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保服务器已启动")
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP错误: {e}")
    except Exception as e:
        print(f"❌ 发生错误: {e}")


async def example_stream_usage():
    """流式使用示例"""
    print("🚀 训练任务深度研究 - 流式使用示例")
    print("=" * 50)
    
    # 创建客户端
    client = TrainingAgentClient()
    
    # 任务ID (替换为您的实际任务ID)
    task_id = "train-20241201-002"
    
    # 集群配置
    cluster_config = {
        "cluster_api_url": "http://localhost:8080",
        "auth_token": None,
        "timeout": 30
    }
    
    try:
        print(f"📋 开始流式研究任务 {task_id}...")
        await client.stream_research(
            task_id=task_id,
            analysis_depth="comprehensive",
            cluster_config=cluster_config
        )
        
        # 研究完成后获取报告
        print("\n📋 获取最终报告...")
        report_data = client.get_research_report(task_id)
        
        if report_data.get("report"):
            filename = f"stream_research_report_{task_id}.md"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(report_data["report"])
            print(f"💾 报告已保存到文件: {filename}")
            
    except aiohttp.ClientError:
        print("❌ 无法连接到服务器，请确保服务器已启动")
    except Exception as e:
        print(f"❌ 发生错误: {e}")


def example_batch_analysis():
    """批量分析示例"""
    print("🚀 训练任务深度研究 - 批量分析示例")
    print("=" * 50)
    
    # 要分析的任务ID列表
    task_ids = [
        "train-20241201-001",
        "train-20241201-002", 
        "train-20241201-003"
    ]
    
    client = TrainingAgentClient()
    
    # 为每个任务启动研究
    for task_id in task_ids:
        try:
            print(f"📋 启动任务 {task_id} 的研究...")
            result = client.start_research_async(task_id=task_id)
            print(f"✅ {result['message']}")
        except Exception as e:
            print(f"❌ 启动任务 {task_id} 失败: {e}")
    
    print(f"\n🔍 监控 {len(task_ids)} 个任务的进度...")
    
    # 监控所有任务状态
    completed_tasks = set()
    while len(completed_tasks) < len(task_ids):
        print(f"\n📊 当前状态 ({len(completed_tasks)}/{len(task_ids)} 完成):")
        
        for task_id in task_ids:
            if task_id in completed_tasks:
                continue
                
            try:
                status = client.get_research_status(task_id)
                progress = status.get("progress", 0)
                task_status = status.get("status", "unknown")
                
                print(f"  {task_id}: {progress:.1%} ({task_status})")
                
                if task_status in ["completed", "failed"]:
                    completed_tasks.add(task_id)
                    
            except Exception as e:
                print(f"  {task_id}: 获取状态失败 - {e}")
        
        if len(completed_tasks) < len(task_ids):
            time.sleep(5)  # 等待5秒后再次检查
    
    print("\n📋 生成批量报告...")
    for task_id in task_ids:
        try:
            report_data = client.get_research_report(task_id)
            if report_data.get("report"):
                filename = f"batch_report_{task_id}.md"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(report_data["report"])
                print(f"💾 {task_id} 报告已保存: {filename}")
        except Exception as e:
            print(f"❌ 获取 {task_id} 报告失败: {e}")


def check_server_health():
    """检查服务器健康状态"""
    try:
        response = requests.get("http://localhost:8000/api/health")
        response.raise_for_status()
        health_data = response.json()
        print("✅ 服务器状态:", health_data["status"])
        return True
    except:
        print("❌ 服务器未响应，请确保服务器已启动:")
        print("   uvicorn src.server.app:app --host 0.0.0.0 --port 8000")
        return False


if __name__ == "__main__":
    print("🤖 Training Task Deep Research Agent - 使用示例")
    print("=" * 60)
    
    # 检查服务器状态
    if not check_server_health():
        exit(1)
    
    print("\n选择使用示例:")
    print("1. 同步使用示例")
    print("2. 流式使用示例") 
    print("3. 批量分析示例")
    
    choice = input("\n请输入选择 (1-3): ").strip()
    
    if choice == "1":
        example_sync_usage()
    elif choice == "2":
        asyncio.run(example_stream_usage())
    elif choice == "3":
        example_batch_analysis()
    else:
        print("❌ 无效选择")
        exit(1)
    
    print("\n🎉 示例执行完成!")