#!/usr/bin/env python3
"""
Training Task Deep Research Agent - RAG功能使用示例

本示例展示如何使用RAG（检索增强生成）功能来增强训练任务分析。
"""

import asyncio
from datetime import datetime
from typing import List

from src.rag.knowledge_retriever import (
    create_knowledge_retriever,
    TrainingKnowledge,
    VectorKnowledgeRetriever,
    HistoricalDataRetriever
)


async def example_knowledge_creation():
    """示例：创建和管理训练知识库"""
    print("🧠 RAG知识库创建示例")
    print("=" * 50)
    
    # 创建一些示例训练知识
    knowledge_base = [
        TrainingKnowledge(
            content="BERT模型在IMDB情感分类任务上的成功训练经验。使用Adam优化器，学习率1e-5，批次大小32。遇到了损失停滞问题，通过降低学习率解决。",
            task_id="bert-imdb-001",
            task_type="classification",
            model_architecture="bert-base-uncased",
            dataset_info="IMDB电影评论数据集，25000条训练样本",
            performance_metrics={"accuracy": 0.92, "f1": 0.91, "loss": 0.15},
            resource_usage={"gpu_memory": 6.5, "gpu_utilization": 0.85, "training_time": 120},
            issues_encountered=["训练损失在第10个epoch后停滞", "初始学习率过高导致震荡"],
            solutions_applied=["降低学习率从2e-5到1e-5", "增加warmup步数到1000", "使用余弦退火调度器"],
            optimization_tips=[
                "使用梯度累积增大有效批次大小",
                "应用dropout防止过拟合",
                "监控验证集性能设置早停"
            ],
            timestamp=datetime.now(),
            tags=["bert", "nlp", "classification", "sentiment_analysis"]
        ),
        
        TrainingKnowledge(
            content="ResNet50在ImageNet数据集上的优化训练。解决了GPU内存不足和过拟合问题。",
            task_id="resnet-imagenet-002",
            task_type="classification",
            model_architecture="resnet50",
            dataset_info="ImageNet 2012，1000类图像分类",
            performance_metrics={"accuracy": 0.88, "top5_acc": 0.96, "loss": 0.25},
            resource_usage={"gpu_memory": 8.2, "gpu_utilization": 0.92, "training_time": 480},
            issues_encountered=["GPU内存不足", "验证准确率下降表明过拟合"],
            solutions_applied=[
                "减少批次大小从64到32",
                "启用混合精度训练",
                "增加数据增强",
                "使用标签平滑"
            ],
            optimization_tips=[
                "使用混合精度训练节省内存",
                "应用数据并行充分利用多GPU",
                "优化数据加载减少I/O瓶颈"
            ],
            timestamp=datetime.now(),
            tags=["resnet", "computer_vision", "classification", "imagenet"]
        ),
        
        TrainingKnowledge(
            content="Transformer模型在机器翻译任务上的训练问题解决方案集合。",
            task_id="transformer-translation-003",
            task_type="translation",
            model_architecture="transformer",
            dataset_info="WMT14 EN-DE翻译数据集",
            performance_metrics={"bleu": 28.5, "loss": 1.2},
            resource_usage={"gpu_memory": 12.0, "gpu_utilization": 0.95, "training_time": 720},
            issues_encountered=["损失发散", "梯度爆炸", "训练不稳定"],
            solutions_applied=[
                "使用梯度裁剪防止梯度爆炸",
                "降低学习率并使用预热",
                "增加层归一化",
                "使用AdamW优化器"
            ],
            optimization_tips=[
                "使用学习率预热和衰减策略",
                "应用标签平滑提高泛化能力",
                "使用梯度检查点技术节省内存"
            ],
            timestamp=datetime.now(),
            tags=["transformer", "nlp", "translation", "seq2seq"]
        )
    ]
    
    # 创建向量检索器
    retriever = create_knowledge_retriever("vector", knowledge_base=knowledge_base)
    print(f"✅ 创建了包含 {len(knowledge_base)} 条知识的向量检索器")
    
    return retriever, knowledge_base


async def example_similar_task_retrieval():
    """示例：检索相似的训练任务"""
    print("\n🔍 相似任务检索示例")
    print("=" * 50)
    
    retriever, _ = await example_knowledge_creation()
    
    # 查询相似任务
    query_task = {
        "model_name": "bert-base-uncased",
        "task_type": "classification", 
        "dataset_name": "imdb"
    }
    
    print(f"查询任务: {query_task}")
    similar_tasks = await retriever.retrieve_similar_tasks(query_task, top_k=3)
    
    print(f"\n找到 {len(similar_tasks)} 个相似任务:")
    for i, task in enumerate(similar_tasks, 1):
        print(f"\n{i}. 任务ID: {task.task_id}")
        print(f"   模型: {task.model_architecture}")
        print(f"   类型: {task.task_type}")
        print(f"   性能: {task.performance_metrics}")
        print(f"   优化建议: {task.optimization_tips[:2]}...")  # 只显示前2条


async def example_solution_retrieval():
    """示例：检索问题解决方案"""
    print("\n🔧 问题解决方案检索示例")
    print("=" * 50)
    
    retriever, _ = await example_knowledge_creation()
    
    # 测试不同的问题查询
    problems = [
        "训练损失停滞不下降",
        "GPU内存不足错误",
        "梯度爆炸导致训练不稳定",
        "模型过拟合验证集性能下降"
    ]
    
    for problem in problems:
        print(f"\n问题: {problem}")
        solutions = await retriever.retrieve_solutions(problem, top_k=2)
        
        if solutions:
            print(f"找到 {len(solutions)} 个解决方案:")
            for i, solution in enumerate(solutions, 1):
                print(f"  {i}. 来源任务: {solution.task_id}")
                print(f"     解决方案: {solution.solutions_applied}")
        else:
            print("  ❌ 未找到相关解决方案")


async def example_optimization_tips_retrieval():
    """示例：检索优化建议"""
    print("\n💡 优化建议检索示例")
    print("=" * 50)
    
    retriever, _ = await example_knowledge_creation()
    
    # 测试不同的上下文
    contexts = [
        {
            "loss_trend": "plateau",
            "description": "损失停滞场景"
        },
        {
            "resource_usage": {"gpu_usage": 0.95},
            "description": "高GPU使用率场景"
        },
        {
            "loss_trend": "diverging",
            "description": "损失发散场景"
        }
    ]
    
    for context in contexts:
        print(f"\n场景: {context['description']}")
        print(f"上下文: {context}")
        
        tips = await retriever.retrieve_optimization_tips(context, top_k=5)
        
        if tips:
            print(f"获得 {len(tips)} 条优化建议:")
            for i, tip in enumerate(tips, 1):
                print(f"  {i}. {tip}")
        else:
            print("  ❌ 未找到相关优化建议")


async def example_historical_data_retriever():
    """示例：历史数据检索器"""
    print("\n📚 历史数据检索器示例")
    print("=" * 50)
    
    # 创建历史数据检索器
    historical_retriever = create_knowledge_retriever("historical")
    
    # 测试相似任务检索
    query_task = {
        "model_name": "bert",
        "task_type": "classification"
    }
    
    print(f"查询任务: {query_task}")
    similar_tasks = await historical_retriever.retrieve_similar_tasks(query_task)
    
    print(f"从历史数据找到 {len(similar_tasks)} 个相似任务:")
    for task in similar_tasks:
        print(f"- {task.task_id}: {task.model_architecture} ({task.task_type})")
        print(f"  性能: {task.performance_metrics}")


async def example_knowledge_base_expansion():
    """示例：动态扩展知识库"""
    print("\n📈 知识库动态扩展示例")
    print("=" * 50)
    
    retriever, _ = await example_knowledge_creation()
    
    # 添加新的知识条目
    new_knowledge = TrainingKnowledge(
        content="GPT-2模型在文本生成任务上的微调经验。解决了生成重复和不连贯的问题。",
        task_id="gpt2-generation-004",
        task_type="generation",
        model_architecture="gpt2-medium",
        dataset_info="自定义文本生成数据集",
        performance_metrics={"perplexity": 25.3, "bleu": 0.45},
        resource_usage={"gpu_memory": 10.5, "gpu_utilization": 0.88, "training_time": 300},
        issues_encountered=["生成文本重复", "输出不连贯", "训练不稳定"],
        solutions_applied=[
            "使用nucleus sampling(top-p)",
            "调整temperature参数",
            "增加序列长度多样性",
            "使用更大的学习率衰减"
        ],
        optimization_tips=[
            "使用beam search改善生成质量",
            "应用长度惩罚避免过短生成",
            "使用BLEU和ROUGE评估生成质量"
        ],
        timestamp=datetime.now(),
        tags=["gpt2", "nlp", "generation", "language_model"]
    )
    
    if isinstance(retriever, VectorKnowledgeRetriever):
        await retriever.add_knowledge(new_knowledge)
        print(f"✅ 成功添加新知识条目: {new_knowledge.task_id}")
        
        # 测试新添加的知识是否可以检索到
        query_task = {
            "model_name": "gpt2",
            "task_type": "generation"
        }
        
        similar_tasks = await retriever.retrieve_similar_tasks(query_task, top_k=2)
        print(f"\n查询 GPT-2 生成任务，找到 {len(similar_tasks)} 个相似任务:")
        for task in similar_tasks:
            print(f"- {task.task_id}: {task.model_architecture}")
    else:
        print("⚠️ 当前检索器不支持动态添加知识")


async def example_comprehensive_analysis():
    """示例：综合分析场景"""
    print("\n🎯 综合分析场景示例")
    print("=" * 50)
    
    retriever, _ = await example_knowledge_creation()
    
    # 模拟一个遇到问题的训练任务
    current_task = {
        "task_id": "current-bert-005",
        "model_name": "bert-base-uncased",
        "task_type": "classification",
        "dataset_name": "custom_dataset",
        "issues": [
            "训练损失在第15个epoch后停滞在0.3",
            "验证准确率开始下降",
            "GPU利用率只有60%"
        ]
    }
    
    print(f"当前任务: {current_task['task_id']}")
    print(f"遇到的问题: {current_task['issues']}")
    
    # 1. 检索相似任务经验
    similar_tasks = await retriever.retrieve_similar_tasks(current_task, top_k=2)
    print(f"\n📋 相似任务经验 ({len(similar_tasks)} 个):")
    for task in similar_tasks:
        print(f"- {task.task_id}: 准确率 {task.performance_metrics.get('accuracy', 'N/A')}")
        print(f"  经验: {task.optimization_tips[0] if task.optimization_tips else '无'}")
    
    # 2. 检索具体问题的解决方案
    all_solutions = []
    for issue in current_task["issues"]:
        solutions = await retriever.retrieve_solutions(issue, top_k=1)
        all_solutions.extend(solutions)
    
    print(f"\n🔧 问题解决方案 ({len(all_solutions)} 个):")
    for solution in all_solutions:
        print(f"- 来源: {solution.task_id}")
        print(f"  方案: {solution.solutions_applied[:2]}")  # 显示前2个
    
    # 3. 检索优化建议
    context = {
        "loss_trend": "plateau",
        "resource_usage": {"gpu_usage": 0.6}
    }
    
    tips = await retriever.retrieve_optimization_tips(context, top_k=3)
    print(f"\n💡 优化建议 ({len(tips)} 条):")
    for i, tip in enumerate(tips, 1):
        print(f"{i}. {tip}")
    
    # 4. 生成综合建议报告
    print(f"\n📊 综合建议报告:")
    print(f"基于 {len(similar_tasks)} 个相似任务和 {len(all_solutions)} 个解决方案:")
    print("1. 损失停滞可能需要调整学习率或优化器")
    print("2. 验证准确率下降表明可能过拟合，需要正则化")
    print("3. GPU利用率低表明可以增大批次大小或使用更复杂模型")


async def main():
    """主函数：运行所有RAG示例"""
    print("🧠 Training Task Deep Research Agent - RAG功能示例")
    print("=" * 70)
    
    try:
        # 运行各种示例
        await example_knowledge_creation()
        await example_similar_task_retrieval()
        await example_solution_retrieval()
        await example_optimization_tips_retrieval()
        await example_historical_data_retriever()
        await example_knowledge_base_expansion()
        await example_comprehensive_analysis()
        
        print("\n🎉 所有RAG示例执行完成!")
        print("\n📝 总结:")
        print("- ✅ 知识库创建和管理")
        print("- ✅ 相似任务检索")
        print("- ✅ 问题解决方案检索")
        print("- ✅ 优化建议检索")
        print("- ✅ 历史数据检索")
        print("- ✅ 知识库动态扩展")
        print("- ✅ 综合分析场景")
        
    except Exception as e:
        print(f"\n❌ 示例执行失败: {e}")
        print("请确保已安装相关依赖:")
        print("pip install sentence-transformers faiss-cpu")


if __name__ == "__main__":
    asyncio.run(main())