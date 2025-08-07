#!/usr/bin/env python3
"""
LangGraph Command路由机制详细演示

本演示展示Command如何通过节点注册表找到对应的执行函数。
"""

import time
from typing import Dict, Any, Optional


class Command:
    """简化的Command类"""
    def __init__(self, goto: str, update: Dict[str, Any] = None):
        self.goto = goto
        self.update = update or {}
    
    def __repr__(self):
        return f"Command(goto='{self.goto}', update={list(self.update.keys())})"


class SimplifiedLangGraph:
    """简化的LangGraph执行引擎，展示Command路由机制"""
    
    def __init__(self):
        self.node_registry = {}  # 📚 节点注册表: 名称 → 函数映射
        self.state = {}         # 📦 共享状态
        self.execution_log = [] # 📝 执行日志
    
    def add_node(self, name: str, function: callable):
        """注册节点函数 - 这就是 builder.add_node() 做的事情"""
        self.node_registry[name] = function
        print(f"📝 注册节点: '{name}' → {function.__name__}")
        self.log(f"NODE_REGISTERED", f"'{name}' mapped to {function.__name__}")
    
    def log(self, action: str, details: str):
        """记录执行日志"""
        self.execution_log.append({
            "step": len(self.execution_log) + 1,
            "action": action,
            "details": details,
            "timestamp": time.time()
        })
    
    def show_registry(self):
        """显示当前的节点注册表"""
        print(f"\n📚 当前节点注册表:")
        for name, func in self.node_registry.items():
            print(f"  '{name}' → {func.__name__}")
    
    def execute_command(self, command: Command) -> Optional[Command]:
        """执行Command - LangGraph的核心路由机制"""
        print(f"\n🔧 处理Command: {command}")
        self.log("COMMAND_RECEIVED", f"goto='{command.goto}'")
        
        # 步骤1: 应用状态更新
        if command.update:
            print(f"📦 更新状态: {list(command.update.keys())}")
            self.state.update(command.update)
            self.log("STATE_UPDATED", f"keys: {list(command.update.keys())}")
        
        # 步骤2: 查找目标节点函数
        print(f"🔍 在注册表中查找节点: '{command.goto}'")
        target_function = self.node_registry.get(command.goto)
        
        if not target_function:
            print(f"❌ 错误: 节点 '{command.goto}' 未找到!")
            print(f"   可用节点: {list(self.node_registry.keys())}")
            self.log("NODE_NOT_FOUND", f"'{command.goto}' not in registry")
            return None
        
        print(f"🎯 找到目标函数: {target_function.__name__}")
        self.log("NODE_FOUND", f"'{command.goto}' → {target_function.__name__}")
        
        # 步骤3: 调用目标函数
        try:
            print(f"⚡ 调用函数: {target_function.__name__}(state)")
            next_command = target_function(self.state)  # 🔑 关键调用
            print(f"✅ 函数执行完成，返回: {next_command}")
            self.log("FUNCTION_EXECUTED", f"{target_function.__name__} returned {next_command}")
            return next_command
        except Exception as e:
            print(f"❌ 函数执行失败: {e}")
            self.log("FUNCTION_ERROR", f"{target_function.__name__}: {e}")
            return None
    
    def run_workflow(self, start_command: Command):
        """运行完整工作流"""
        print("🚀 启动工作流执行引擎...")
        print("=" * 60)
        
        current_command = start_command
        step = 1
        max_steps = 10  # 安全限制
        
        while current_command and current_command.goto != "__end__" and step <= max_steps:
            print(f"\n🔄 === 执行步骤 {step} ===")
            current_command = self.execute_command(current_command)
            step += 1
            
            if current_command:
                print(f"📋 下一步将执行: {current_command.goto}")
            else:
                print(f"⚠️ 工作流中断")
                break
            
            time.sleep(0.5)  # 便于观察
        
        if step > max_steps:
            print("⚠️ 达到最大步数限制，强制停止")
        
        print(f"\n🎉 工作流执行完成!")
        self.show_final_results()
    
    def show_final_results(self):
        """显示最终结果"""
        print(f"\n📊 执行结果:")
        print(f"- 最终状态: {self.state}")
        print(f"- 执行步数: {len(self.execution_log)}")
        
        print(f"\n📝 详细执行日志:")
        for log in self.execution_log:
            print(f"  {log['step']:2d}. [{log['action']}] {log['details']}")


# ==================== 演示节点函数 ====================

def coordinator_node(state: Dict[str, Any]) -> Command:
    """协调器节点 - 解析任务并启动规划"""
    print("  🎯 [Coordinator] 解析任务ID并启动流程")
    task_id = state.get("task_id", "demo-task-001")
    
    return Command(
        goto="planner",
        update={
            "task_id": task_id,
            "research_topic": f"Analysis of task {task_id}",
            "observations": ["Coordinator started"]
        }
    )


def planner_node(state: Dict[str, Any]) -> Command:
    """规划器节点 - 生成研究计划"""
    print("  📋 [Planner] 生成6步研究计划")
    task_id = state.get("task_id", "unknown")
    
    plan = {
        "title": f"Task {task_id} Analysis Plan",
        "steps": [
            {"name": "task_info", "completed": False},
            {"name": "performance", "completed": False}, 
            {"name": "resource", "completed": False},
            {"name": "logs", "completed": False},
            {"name": "diagnosis", "completed": False},
            {"name": "optimization", "completed": False}
        ]
    }
    
    return Command(
        goto="dynamic_executor",
        update={
            "current_plan": plan,
            "plan_iterations": 1,
            "observations": state.get("observations", []) + ["Plan generated"]
        }
    )


def dynamic_executor_node(state: Dict[str, Any]) -> Command:
    """动态执行器节点 - 执行计划中的步骤"""
    print("  🔧 [Dynamic Executor] 执行计划步骤")
    
    current_plan = state.get("current_plan", {})
    steps = current_plan.get("steps", [])
    
    # 查找下一个未完成的步骤
    next_step = None
    for step in steps:
        if not step.get("completed", False):
            next_step = step
            break
    
    if not next_step:
        print("    ✅ 所有步骤已完成，转向报告器")
        return Command(
            goto="reporter",
            update={"status": "all_steps_completed"}
        )
    
    # 模拟执行步骤
    step_name = next_step["name"]
    print(f"    🔄 执行步骤: {step_name}")
    
    # 标记步骤为已完成
    next_step["completed"] = True
    
    # 模拟步骤结果
    step_results = {
        "task_info": {"status": "running", "model": "bert-base"},
        "performance": {"loss": 0.25, "accuracy": 0.89},
        "resource": {"gpu_usage": "85%", "memory": "12GB"},
        "logs": {"errors": 3, "warnings": 12},
        "diagnosis": {"issues": ["high GPU usage", "memory near limit"]},
        "optimization": {"tips": ["reduce batch size", "enable gradient accumulation"]}
    }
    
    result = step_results.get(step_name, {"result": "completed"})
    
    # 检查是否还有剩余步骤
    remaining_steps = [s for s in steps if not s.get("completed", False)]
    observations = state.get("observations", [])
    observations.append(f"Completed: {step_name}")
    
    if remaining_steps:
        print(f"    📋 剩余步骤: {len(remaining_steps)}个，继续执行")
        return Command(
            goto="dynamic_executor",  # 🔄 自循环
            update={
                "current_plan": current_plan,
                "observations": observations,
                f"{step_name}_result": result
            }
        )
    else:
        print(f"    🏁 所有步骤完成，转向报告器")
        return Command(
            goto="reporter",
            update={
                "current_plan": current_plan,
                "observations": observations,
                f"{step_name}_result": result
            }
        )


def reporter_node(state: Dict[str, Any]) -> Command:
    """报告器节点 - 生成最终报告"""
    print("  📊 [Reporter] 生成综合分析报告")
    
    current_plan = state.get("current_plan", {})
    observations = state.get("observations", [])
    completed_steps = len([s for s in current_plan.get("steps", []) if s.get("completed", False)])
    
    report = {
        "task_id": state.get("task_id"),
        "plan_title": current_plan.get("title"),
        "completed_steps": completed_steps,
        "total_steps": len(current_plan.get("steps", [])),
        "success_rate": f"{completed_steps}/{len(current_plan.get('steps', []))}",
        "observations_count": len(observations),
        "summary": f"Successfully analyzed task with {completed_steps} analysis steps"
    }
    
    return Command(
        goto="__end__",
        update={"final_report": report}
    )


# ==================== 主演示程序 ====================

def demo_node_registration():
    """演示节点注册过程"""
    print("🔧 演示1: 节点注册机制")
    print("=" * 40)
    
    engine = SimplifiedLangGraph()
    
    print("🏗️ 开始注册节点...")
    engine.add_node("coordinator", coordinator_node)
    engine.add_node("planner", planner_node) 
    engine.add_node("dynamic_executor", dynamic_executor_node)
    engine.add_node("reporter", reporter_node)
    
    engine.show_registry()
    
    print(f"\n💡 解释:")
    print(f"- add_node() 在内部建立了 '节点名称' → '函数对象' 的映射")
    print(f"- 当Command指定goto='planner'时，会查找并调用planner_node函数")
    
    return engine


def demo_command_routing():
    """演示Command路由机制"""
    print(f"\n\n🎯 演示2: Command路由机制")
    print("=" * 40)
    
    engine = demo_node_registration()
    
    print(f"\n🚀 模拟手动执行单个Command...")
    
    # 手动执行一个Command
    test_command = Command(
        goto="planner",
        update={"task_id": "manual-test-001"}
    )
    
    print(f"📋 测试Command: {test_command}")
    result_command = engine.execute_command(test_command)
    
    print(f"\n💡 解释:")
    print(f"1. Command包含goto='planner'")
    print(f"2. LangGraph查找node_registry['planner']")
    print(f"3. 找到planner_node函数")
    print(f"4. 调用planner_node(state)并获得返回的Command")
    
    return engine


def demo_complete_workflow():
    """演示完整工作流"""
    print(f"\n\n🔄 演示3: 完整工作流执行")
    print("=" * 40)
    
    engine = SimplifiedLangGraph()
    
    # 注册所有节点
    engine.add_node("coordinator", coordinator_node)
    engine.add_node("planner", planner_node)
    engine.add_node("dynamic_executor", dynamic_executor_node) 
    engine.add_node("reporter", reporter_node)
    
    # 启动工作流
    start_command = Command(
        goto="coordinator",
        update={"task_id": "workflow-demo-001"}
    )
    
    engine.run_workflow(start_command)


def explain_mechanism():
    """解释核心机制"""
    print(f"\n\n🔑 核心机制总结")
    print("=" * 40)
    
    print(f"""
🏗️ LangGraph内部机制:

1. 📚 节点注册阶段:
   builder.add_node("coordinator", coordinator_node)
   ↓
   node_registry["coordinator"] = coordinator_node

2. 🎯 Command路由阶段:  
   Command(goto="coordinator", update={{...}})
   ↓
   target_function = node_registry["coordinator"]  # 查找函数
   ↓
   next_command = target_function(state)  # 调用函数

3. 🔄 循环执行:
   每个节点返回Command指定下一个节点
   ↓
   LangGraph继续查找和调用
   ↓
   直到goto="__end__"

📞 类比 - 电话簿系统:
- add_node = 在电话簿记录 "姓名 → 电话号码"
- Command(goto="姓名") = 要给某人打电话
- LangGraph = 查电话簿找到号码并拨打

🎯 回答您的问题:
"Command如何知道用什么来执行？"
→ 通过node_registry映射表查找对应的函数！
""")


def main():
    """主演示函数"""
    print("🤖 LangGraph Command路由机制深度演示")
    print("=" * 60)
    
    # 运行各种演示
    demo_node_registration()
    demo_command_routing() 
    demo_complete_workflow()
    explain_mechanism()
    
    print(f"\n🎉 演示完成！现在您应该清楚Command是如何找到对应执行函数的了！")


if __name__ == "__main__":
    main()