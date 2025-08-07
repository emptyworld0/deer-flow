#!/usr/bin/env python3
"""
LangGraph Command指令流传递机制演示

这个示例展示规划器规划完成后，如何通过Command对象自动指导后续节点执行。
"""

import asyncio
import json
from typing import Literal, Dict, Any
from langgraph.types import Command
from langchain_core.runnables import RunnableConfig

# 模拟我们的类型
from src.graph.types import TrainingAgentState, TrainingPlan, TrainingResearchStep, StepType


class CommandFlowDemo:
    """Command指令流演示类"""
    
    def __init__(self):
        self.execution_log = []  # 记录执行日志
        
    def log_execution(self, node_name: str, action: str, details: str = ""):
        """记录执行步骤"""
        log_entry = {
            "step": len(self.execution_log) + 1,
            "node": node_name,
            "action": action,
            "details": details
        }
        self.execution_log.append(log_entry)
        print(f"📝 步骤 {log_entry['step']}: [{node_name}] {action}")
        if details:
            print(f"   详情: {details}")
    
    def simulate_planner_node(self, state: Dict[str, Any]) -> Command:
        """模拟规划器节点 - 关键：生成计划并返回Command"""
        self.log_execution("planner", "开始规划", "生成6步研究计划")
        
        # 创建研究计划
        plan = {
            "title": f"任务 {state.get('task_id', 'demo-task')} 深度分析计划",
            "steps": [
                {"title": "获取任务信息", "type": "task_info", "completed": False},
                {"title": "性能分析", "type": "performance", "completed": False},
                {"title": "资源分析", "type": "resource", "completed": False},
                {"title": "日志分析", "type": "log", "completed": False},
                {"title": "错误诊断", "type": "diagnosis", "completed": False},
                {"title": "优化建议", "type": "optimization", "completed": False}
            ]
        }
        
        self.log_execution("planner", "规划完成", f"生成了{len(plan['steps'])}个步骤")
        
        # 🔑 关键：通过Command指定下一个节点
        return Command(
            goto="dynamic_executor",  # 指令：下一步执行动态执行器
            update={                   # 数据：把计划存入state
                "current_plan": plan,
                "plan_iterations": state.get("plan_iterations", 0) + 1,
                "observations": state.get("observations", []) + ["Plan generated"]
            }
        )
    
    def get_next_unfinished_step(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """获取下一个未完成的步骤"""
        if not plan or "steps" not in plan:
            return None
        
        for step in plan["steps"]:
            if not step.get("completed", False):
                return step
        return None
    
    def simulate_step_execution(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """模拟执行一个步骤"""
        step_type = step.get("type", "unknown")
        
        # 模拟不同类型步骤的执行结果
        execution_results = {
            "task_info": {"task_status": "running", "model": "bert-base", "dataset": "imdb"},
            "performance": {"loss": 0.245, "accuracy": 0.892, "trend": "improving"},
            "resource": {"gpu_usage": "85%", "memory_usage": "12GB/16GB"},
            "log": {"error_count": 3, "warning_count": 12},
            "diagnosis": {"issues_found": ["高GPU使用率", "内存接近上限"]},
            "optimization": {"recommendations": ["降低batch_size", "启用梯度累积"]}
        }
        
        result = execution_results.get(step_type, {"result": "completed"})
        step["completed"] = True  # 标记为已完成
        step["execution_result"] = result
        
        return result
    
    def simulate_dynamic_executor_node(self, state: Dict[str, Any]) -> Command:
        """模拟动态执行器节点 - 关键：自循环执行计划中的步骤"""
        current_plan = state.get("current_plan")
        
        if not current_plan:
            self.log_execution("dynamic_executor", "错误", "没有找到执行计划")
            return Command(goto="reporter", update={"error": "No plan found"})
        
        # 🔑 获取下一个要执行的步骤
        next_step = self.get_next_unfinished_step(current_plan)
        
        if not next_step:
            self.log_execution("dynamic_executor", "完成", "所有步骤已执行完毕")
            return Command(goto="reporter", update={"status": "all_steps_completed"})
        
        # 🔧 执行当前步骤
        step_title = next_step.get("title", "unknown")
        step_type = next_step.get("type", "unknown")
        
        self.log_execution("dynamic_executor", f"执行步骤", f"{step_title} ({step_type})")
        
        # 模拟步骤执行
        step_result = self.simulate_step_execution(next_step)
        
        # 更新observations
        observations = state.get("observations", [])
        observations.append(f"Completed: {step_title}")
        
        # 🔍 检查是否还有剩余步骤
        remaining_step = self.get_next_unfinished_step(current_plan)
        
        update_data = {
            "current_plan": current_plan,
            "observations": observations,
            f"{step_type}_result": step_result  # 存储步骤结果
        }
        
        if remaining_step:
            # 🔄 还有步骤，指令继续执行自己 (自循环)
            self.log_execution("dynamic_executor", "自循环", f"剩余步骤: {remaining_step['title']}")
            return Command(goto="dynamic_executor", update=update_data)
        else:
            # 🏁 步骤全部完成，指令转到报告器
            self.log_execution("dynamic_executor", "转向报告器", "所有步骤执行完成")
            return Command(goto="reporter", update=update_data)
    
    def simulate_reporter_node(self, state: Dict[str, Any]) -> Command:
        """模拟报告器节点 - 生成最终报告"""
        self.log_execution("reporter", "生成报告", "汇总所有执行结果")
        
        # 收集所有结果
        observations = state.get("observations", [])
        current_plan = state.get("current_plan", {})
        
        # 统计完成的步骤
        completed_steps = 0
        if current_plan and "steps" in current_plan:
            completed_steps = sum(1 for step in current_plan["steps"] if step.get("completed", False))
        
        # 生成报告
        report = {
            "task_id": state.get("task_id", "unknown"),
            "total_steps": len(current_plan.get("steps", [])),
            "completed_steps": completed_steps,
            "success_rate": f"{completed_steps}/{len(current_plan.get('steps', []))}",
            "observations": observations,
            "summary": f"训练任务分析完成，执行了{completed_steps}个分析步骤"
        }
        
        self.log_execution("reporter", "报告生成", f"成功率: {report['success_rate']}")
        
        # 🏁 指令结束工作流
        return Command(
            goto="__end__",
            update={"final_report": report}
        )
    
    async def simulate_conditional_router(self, state: Dict[str, Any]) -> str:
        """模拟条件路由器 - 决定dynamic_executor的下一步"""
        current_plan = state.get("current_plan")
        next_step = self.get_next_unfinished_step(current_plan)
        
        if next_step:
            self.log_execution("router", "路由决策", f"继续执行: {next_step['title']}")
            return "dynamic_executor"  # 继续自循环
        else:
            self.log_execution("router", "路由决策", "转向reporter")
            return "reporter"          # 转到报告器
    
    async def run_complete_workflow(self):
        """运行完整的工作流演示"""
        print("🚀 LangGraph Command指令流演示")
        print("=" * 60)
        
        # 初始状态
        state = {
            "task_id": "demo-task-123",
            "observations": [],
            "plan_iterations": 0
        }
        
        print(f"📋 初始任务ID: {state['task_id']}")
        print(f"\n🔄 开始工作流执行...\n")
        
        # 1. 模拟规划器
        print("1️⃣ 规划器阶段:")
        command1 = self.simulate_planner_node(state)
        print(f"   Command: goto='{command1.goto}', update_keys={list(command1.update.keys())}")
        
        # 应用更新
        state.update(command1.update)
        current_node = command1.goto
        
        # 2. 模拟动态执行器的多次执行
        print(f"\n2️⃣ 动态执行器阶段:")
        execution_round = 1
        
        while current_node == "dynamic_executor":
            print(f"\n   第{execution_round}轮执行:")
            command = self.simulate_dynamic_executor_node(state)
            print(f"   Command: goto='{command.goto}', update_keys={list(command.update.keys())}")
            
            # 应用更新
            state.update(command.update)
            current_node = command.goto
            execution_round += 1
            
            # 安全检查，避免无限循环
            if execution_round > 10:
                print("   ⚠️ 达到最大执行轮数，退出循环")
                break
        
        # 3. 模拟报告器
        if current_node == "reporter":
            print(f"\n3️⃣ 报告器阶段:")
            command_final = self.simulate_reporter_node(state)
            print(f"   Command: goto='{command_final.goto}', update_keys={list(command_final.update.keys())}")
            
            # 应用最终更新
            state.update(command_final.update)
        
        # 显示最终结果
        print(f"\n📊 执行结果摘要:")
        final_report = state.get("final_report", {})
        if final_report:
            print(f"- 任务ID: {final_report.get('task_id')}")
            print(f"- 成功率: {final_report.get('success_rate')}")
            print(f"- 总观察数: {len(final_report.get('observations', []))}")
            print(f"- 摘要: {final_report.get('summary')}")
        
        print(f"\n📝 完整执行日志:")
        for i, log in enumerate(self.execution_log, 1):
            print(f"{i:2d}. [{log['node']}] {log['action']}")
        
        return state
    
    def explain_key_mechanisms(self):
        """解释关键机制"""
        print(f"\n🔑 关键机制解释:")
        print(f"1. Command对象控制流程:")
        print(f"   - planner返回Command(goto='dynamic_executor') 启动执行")
        print(f"   - dynamic_executor返回Command(goto='dynamic_executor') 自循环")
        print(f"   - 最后返回Command(goto='reporter') 转到报告")
        
        print(f"\n2. 状态共享:")
        print(f"   - current_plan在planner中设置，在dynamic_executor中读取")
        print(f"   - 执行结果累积在state中")
        print(f"   - observations记录执行历史")
        
        print(f"\n3. 自动化:")
        print(f"   - 无需人工干预")
        print(f"   - 基于计划自动执行")
        print(f"   - 基于状态自动路由")


async def main():
    """主演示函数"""
    demo = CommandFlowDemo()
    
    # 运行完整工作流
    final_state = await demo.run_complete_workflow()
    
    # 解释机制
    demo.explain_key_mechanisms()
    
    print(f"\n🎉 指令流演示完成！")
    print(f"\n💡 总结:")
    print(f"   规划器通过Command启动 → 动态执行器通过Command自循环 → 报告器通过Command结束")
    print(f"   整个过程完全自动化，无需手动干预！")


if __name__ == "__main__":
    asyncio.run(main())