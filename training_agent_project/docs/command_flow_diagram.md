# LangGraph Command指令流可视化图表

## 🎯 指令传递总览

```mermaid
graph TD
    A[START] --> B[coordinator_node]
    B --> |Command: goto='planner'| C[planner_node]
    C --> |Command: goto='dynamic_executor'| D[dynamic_executor_node]
    D --> |Command: goto='dynamic_executor'| D
    D --> |Command: goto='reporter'| E[reporter_node]
    E --> |Command: goto='__end__'| F[END]

    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style C fill:#e8f5e8
    style D fill:#fff3e0
    style E fill:#fce4ec
    style F fill:#e1f5fe
```

## 🔄 详细执行流程

### 1. 规划器指令
```mermaid
sequenceDiagram
    participant P as planner_node
    participant S as State
    participant DE as dynamic_executor

    P->>P: 生成6步研究计划
    P->>S: 设置 current_plan
    P->>DE: Command(goto="dynamic_executor")
    Note over P,DE: 规划器通过Command启动执行器
```

### 2. 动态执行器自循环
```mermaid
sequenceDiagram
    participant DE as dynamic_executor
    participant S as State
    participant EX as Executors

    loop 每个计划步骤
        DE->>S: 读取 current_plan
        DE->>DE: 获取下一个未执行步骤
        DE->>EX: 执行具体步骤 (TaskInfoExecutor/PerformanceAnalysisExecutor等)
        EX->>DE: 返回执行结果
        DE->>S: 更新执行结果
        
        alt 还有剩余步骤
            DE->>DE: Command(goto="dynamic_executor")
            Note over DE: 自循环继续执行
        else 所有步骤完成
            DE->>Reporter: Command(goto="reporter")
            Note over DE,Reporter: 转向报告器
        end
    end
```

### 3. 状态流转图
```mermaid
stateDiagram-v2
    [*] --> Coordinator
    Coordinator --> Planner: task_id设置完成
    Planner --> DynamicExecutor: current_plan设置完成
    
    state DynamicExecutor {
        [*] --> CheckPlan
        CheckPlan --> ExecuteStep: 有未执行步骤
        ExecuteStep --> UpdateState: 步骤执行完成
        UpdateState --> CheckRemaining: 更新状态
        CheckRemaining --> ExecuteStep: 还有剩余步骤
        CheckRemaining --> [*]: 所有步骤完成
    }
    
    DynamicExecutor --> Reporter: 所有步骤完成
    Reporter --> [*]: 报告生成完成
```

## 📋 具体Command示例

### 规划器 → 动态执行器
```python
# planner_node返回的Command
Command(
    goto="dynamic_executor",
    update={
        "current_plan": {
            "title": "训练任务深度分析计划",
            "steps": [
                {"title": "获取任务信息", "type": "task_info", "completed": False},
                {"title": "性能分析", "type": "performance", "completed": False},
                # ... 更多步骤
            ]
        },
        "plan_iterations": 1,
        "observations": ["Plan generated"]
    }
)
```

### 动态执行器 → 动态执行器 (自循环)
```python
# dynamic_executor_node返回的Command (有剩余步骤)
Command(
    goto="dynamic_executor",
    update={
        "current_plan": updated_plan,  # 更新的计划 (某些步骤已标记完成)
        "observations": ["Completed: 获取任务信息"],
        "task_info_result": {"status": "running", "model": "bert"},
        "training_metrics": [...]
    }
)
```

### 动态执行器 → 报告器
```python
# dynamic_executor_node返回的Command (所有步骤完成)
Command(
    goto="reporter",
    update={
        "current_plan": completed_plan,  # 所有步骤都已完成
        "observations": ["Completed: 优化建议"],
        "optimization_result": {"recommendations": ["降低学习率", "增加batch size"]}
    }
)
```

## 🔑 核心机制总结

### Command对象的三个关键作用：

1. **流程控制** (goto字段)
   - 明确指定下一个要执行的节点
   - 支持条件跳转和循环

2. **数据传递** (update字段)
   - 在节点间传递数据
   - 累积执行结果

3. **状态同步**
   - 所有节点共享同一个State对象
   - 通过update同步最新状态

### 自动化执行的实现：

```
规划完成 ─Command─> 执行启动 ─Command(自循环)─> 逐步执行 ─Command─> 报告生成
    ↑                    ↑                        ↑              ↑
 生成计划           读取计划                  更新进度        汇总结果
```

### 容错和灵活性：

- **单步失败不中断整体流程**
- **可以跳过特定步骤**
- **支持动态计划调整**
- **可以添加新的执行器类型**

这种基于Command的指令流机制确保了从规划到执行的无缝自动化，实现了真正的"计划什么，执行什么"！