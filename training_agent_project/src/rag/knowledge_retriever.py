# Copyright (c) 2025
# SPDX-License-Identifier: MIT

import logging
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore
from langchain_core.embeddings import Embeddings
from langchain_community.vectorstores import FAISS, Chroma
from langchain_community.embeddings import OpenAIEmbeddings, HuggingFaceEmbeddings

logger = logging.getLogger(__name__)


@dataclass
class TrainingKnowledge:
    """训练知识条目"""
    content: str
    task_id: str
    task_type: str  # "classification", "generation", "detection", etc.
    model_architecture: str
    dataset_info: str
    performance_metrics: Dict[str, float]
    resource_usage: Dict[str, float]
    issues_encountered: List[str]
    solutions_applied: List[str]
    optimization_tips: List[str]
    timestamp: datetime
    tags: List[str]


class KnowledgeRetriever(ABC):
    """知识检索器抽象基类"""
    
    @abstractmethod
    async def retrieve_similar_tasks(self, query_task: Dict[str, Any], top_k: int = 5) -> List[TrainingKnowledge]:
        """检索相似的训练任务"""
        pass
    
    @abstractmethod
    async def retrieve_solutions(self, problem_description: str, top_k: int = 3) -> List[TrainingKnowledge]:
        """检索问题解决方案"""
        pass
    
    @abstractmethod
    async def retrieve_optimization_tips(self, context: Dict[str, Any], top_k: int = 5) -> List[str]:
        """检索优化建议"""
        pass


class VectorKnowledgeRetriever(KnowledgeRetriever):
    """基于向量数据库的知识检索器"""
    
    def __init__(
        self,
        vector_store: VectorStore,
        embeddings: Embeddings,
        knowledge_base: List[TrainingKnowledge] = None
    ):
        self.vector_store = vector_store
        self.embeddings = embeddings
        self.knowledge_base = knowledge_base or []
        
    @classmethod
    def create_with_faiss(
        cls,
        embeddings: Embeddings = None,
        knowledge_base: List[TrainingKnowledge] = None
    ):
        """使用FAISS创建检索器"""
        if embeddings is None:
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        
        # 创建初始文档
        documents = []
        if knowledge_base:
            for kb in knowledge_base:
                doc = Document(
                    page_content=kb.content,
                    metadata={
                        "task_id": kb.task_id,
                        "task_type": kb.task_type,
                        "model_architecture": kb.model_architecture,
                        "timestamp": kb.timestamp.isoformat(),
                        "tags": ",".join(kb.tags)
                    }
                )
                documents.append(doc)
        else:
            # 创建一个虚拟文档以初始化向量存储
            documents = [Document(page_content="初始化文档", metadata={})]
        
        vector_store = FAISS.from_documents(documents, embeddings)
        return cls(vector_store, embeddings, knowledge_base)
    
    async def add_knowledge(self, knowledge: TrainingKnowledge):
        """添加新的知识条目"""
        doc = Document(
            page_content=knowledge.content,
            metadata={
                "task_id": knowledge.task_id,
                "task_type": knowledge.task_type,
                "model_architecture": knowledge.model_architecture,
                "timestamp": knowledge.timestamp.isoformat(),
                "tags": ",".join(knowledge.tags)
            }
        )
        self.vector_store.add_documents([doc])
        self.knowledge_base.append(knowledge)
    
    async def retrieve_similar_tasks(self, query_task: Dict[str, Any], top_k: int = 5) -> List[TrainingKnowledge]:
        """检索相似的训练任务"""
        try:
            # 构建查询字符串
            query_parts = []
            if "model_name" in query_task:
                query_parts.append(f"模型: {query_task['model_name']}")
            if "dataset_name" in query_task:
                query_parts.append(f"数据集: {query_task['dataset_name']}")
            if "task_type" in query_task:
                query_parts.append(f"任务类型: {query_task['task_type']}")
            
            query = " ".join(query_parts)
            if not query:
                query = "训练任务"
            
            # 执行相似性搜索
            docs = self.vector_store.similarity_search(query, k=top_k)
            
            # 转换为TrainingKnowledge对象
            similar_tasks = []
            for doc in docs:
                # 从knowledge_base中找到对应的条目
                task_id = doc.metadata.get("task_id")
                for kb in self.knowledge_base:
                    if kb.task_id == task_id:
                        similar_tasks.append(kb)
                        break
            
            logger.info(f"Retrieved {len(similar_tasks)} similar tasks for query: {query}")
            return similar_tasks
            
        except Exception as e:
            logger.error(f"Error retrieving similar tasks: {e}")
            return []
    
    async def retrieve_solutions(self, problem_description: str, top_k: int = 3) -> List[TrainingKnowledge]:
        """检索问题解决方案"""
        try:
            # 添加问题关键词以提高检索准确性
            enhanced_query = f"问题 错误 解决方案 {problem_description}"
            
            docs = self.vector_store.similarity_search(enhanced_query, k=top_k * 2)  # 获取更多候选
            
            # 过滤有解决方案的知识条目
            solutions = []
            for doc in docs:
                task_id = doc.metadata.get("task_id")
                for kb in self.knowledge_base:
                    if kb.task_id == task_id and kb.solutions_applied:
                        solutions.append(kb)
                        if len(solutions) >= top_k:
                            break
                if len(solutions) >= top_k:
                    break
            
            logger.info(f"Retrieved {len(solutions)} solutions for problem: {problem_description[:50]}...")
            return solutions
            
        except Exception as e:
            logger.error(f"Error retrieving solutions: {e}")
            return []
    
    async def retrieve_optimization_tips(self, context: Dict[str, Any], top_k: int = 5) -> List[str]:
        """检索优化建议"""
        try:
            # 构建优化查询
            query_parts = ["优化", "性能提升", "加速训练"]
            
            if "loss_trend" in context:
                if context["loss_trend"] == "plateau":
                    query_parts.append("损失停滞")
                elif context["loss_trend"] == "diverging":
                    query_parts.append("损失发散")
            
            if "resource_usage" in context:
                if context["resource_usage"].get("gpu_usage", 0) > 0.9:
                    query_parts.append("GPU优化")
                elif context["resource_usage"].get("gpu_usage", 0) < 0.3:
                    query_parts.append("资源利用率")
            
            query = " ".join(query_parts)
            docs = self.vector_store.similarity_search(query, k=top_k * 2)
            
            # 提取优化建议
            tips = []
            for doc in docs:
                task_id = doc.metadata.get("task_id")
                for kb in self.knowledge_base:
                    if kb.task_id == task_id:
                        tips.extend(kb.optimization_tips)
            
            # 去重并限制数量
            unique_tips = list(dict.fromkeys(tips))[:top_k]
            
            logger.info(f"Retrieved {len(unique_tips)} optimization tips")
            return unique_tips
            
        except Exception as e:
            logger.error(f"Error retrieving optimization tips: {e}")
            return []


class HistoricalDataRetriever(KnowledgeRetriever):
    """历史数据检索器 - 从数据库或文件系统检索"""
    
    def __init__(self, data_source: str = "database"):
        self.data_source = data_source
        # 这里可以连接到实际的历史数据存储
        
    async def retrieve_similar_tasks(self, query_task: Dict[str, Any], top_k: int = 5) -> List[TrainingKnowledge]:
        """从历史数据库检索相似任务"""
        # 模拟数据库查询
        # 实际实现中应该连接到真实的历史数据存储
        
        sample_knowledge = [
            TrainingKnowledge(
                content="BERT模型在文本分类任务上的训练经验，使用Adam优化器，学习率1e-5，批次大小32",
                task_id="hist-bert-001",
                task_type="classification",
                model_architecture="bert-base-uncased",
                dataset_info="IMDB电影评论数据集",
                performance_metrics={"accuracy": 0.92, "f1": 0.91, "loss": 0.15},
                resource_usage={"gpu_memory": 6.5, "gpu_utilization": 0.85, "training_time": 120},
                issues_encountered=["初始学习率过高导致损失震荡"],
                solutions_applied=["降低学习率到1e-5", "增加warmup步数"],
                optimization_tips=["使用梯度累积以增大有效批次大小", "应用学习率调度器"],
                timestamp=datetime.now(),
                tags=["bert", "classification", "nlp"]
            ),
            TrainingKnowledge(
                content="ResNet50在图像分类上的训练优化，解决了过拟合问题",
                task_id="hist-resnet-002",
                task_type="classification",
                model_architecture="resnet50",
                dataset_info="ImageNet子集",
                performance_metrics={"accuracy": 0.88, "top5_acc": 0.96, "loss": 0.25},
                resource_usage={"gpu_memory": 8.2, "gpu_utilization": 0.92, "training_time": 180},
                issues_encountered=["验证集准确率下降，出现过拟合"],
                solutions_applied=["增加数据增强", "使用DropOut", "减少模型复杂度"],
                optimization_tips=["使用混合精度训练", "优化数据加载管道"],
                timestamp=datetime.now(),
                tags=["resnet", "classification", "computer_vision"]
            )
        ]
        
        # 简单的相似性匹配 (实际应该使用更复杂的匹配算法)
        model_name = query_task.get("model_name", "").lower()
        task_type = query_task.get("task_type", "").lower()
        
        filtered_knowledge = []
        for kb in sample_knowledge:
            score = 0
            if model_name in kb.model_architecture.lower():
                score += 3
            if task_type in kb.task_type.lower():
                score += 2
            
            if score > 0:
                filtered_knowledge.append(kb)
        
        return filtered_knowledge[:top_k]
    
    async def retrieve_solutions(self, problem_description: str, top_k: int = 3) -> List[TrainingKnowledge]:
        """检索问题解决方案"""
        # 模拟解决方案检索
        problem_lower = problem_description.lower()
        
        solution_knowledge = []
        
        if "loss" in problem_lower and ("plateau" in problem_lower or "停滞" in problem_lower):
            solution_knowledge.append(TrainingKnowledge(
                content="损失停滞问题的解决方案合集",
                task_id="solution-001",
                task_type="general",
                model_architecture="general",
                dataset_info="multiple",
                performance_metrics={},
                resource_usage={},
                issues_encountered=["训练损失停滞不下降"],
                solutions_applied=[
                    "降低学习率或使用学习率调度器",
                    "检查数据预处理是否正确",
                    "增加模型复杂度或调整架构",
                    "使用不同的优化器（如AdamW替代Adam）"
                ],
                optimization_tips=[
                    "使用余弦退火学习率调度",
                    "尝试不同的损失函数",
                    "增加正则化以防止过拟合"
                ],
                timestamp=datetime.now(),
                tags=["loss_plateau", "optimization"]
            ))
        
        if "memory" in problem_lower or "oom" in problem_lower or "内存" in problem_lower:
            solution_knowledge.append(TrainingKnowledge(
                content="GPU内存不足问题的解决方案",
                task_id="solution-002",
                task_type="general",
                model_architecture="general",
                dataset_info="multiple",
                performance_metrics={},
                resource_usage={},
                issues_encountered=["GPU内存不足", "CUDA out of memory"],
                solutions_applied=[
                    "减少批次大小",
                    "使用梯度累积",
                    "启用混合精度训练",
                    "优化模型架构"
                ],
                optimization_tips=[
                    "使用梯度检查点技术",
                    "清理不必要的中间变量",
                    "使用更高效的数据加载器"
                ],
                timestamp=datetime.now(),
                tags=["memory", "optimization", "gpu"]
            ))
        
        return solution_knowledge[:top_k]
    
    async def retrieve_optimization_tips(self, context: Dict[str, Any], top_k: int = 5) -> List[str]:
        """检索优化建议"""
        tips = [
            "使用混合精度训练可以减少内存使用并加速训练",
            "应用数据并行和模型并行来充分利用多GPU",
            "使用预训练模型作为起点可以显著减少训练时间",
            "定期保存检查点以防止训练中断导致的时间损失",
            "监控训练指标并设置早停机制避免过拟合",
            "使用学习率调度器来获得更好的收敛效果",
            "优化数据加载管道以减少I/O瓶颈",
            "使用适当的批次大小平衡内存使用和训练稳定性"
        ]
        
        # 根据上下文过滤相关建议
        relevant_tips = []
        
        if context.get("gpu_usage", 0) > 0.9:
            relevant_tips.extend([
                "考虑减少批次大小以降低GPU内存使用",
                "启用混合精度训练以优化内存效率"
            ])
        
        if context.get("training_time", 0) > 1000:  # 训练时间过长
            relevant_tips.extend([
                "使用预训练模型加速收敛",
                "考虑增加学习率以加快训练速度"
            ])
        
        # 合并通用建议和特定建议
        all_tips = relevant_tips + tips
        return list(dict.fromkeys(all_tips))[:top_k]  # 去重并限制数量


def create_knowledge_retriever(
    retriever_type: str = "vector",
    embeddings_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    knowledge_base: List[TrainingKnowledge] = None
) -> KnowledgeRetriever:
    """创建知识检索器工厂函数"""
    
    if retriever_type == "vector":
        embeddings = HuggingFaceEmbeddings(model_name=embeddings_model)
        return VectorKnowledgeRetriever.create_with_faiss(embeddings, knowledge_base)
    elif retriever_type == "historical":
        return HistoricalDataRetriever()
    else:
        raise ValueError(f"Unknown retriever type: {retriever_type}")


# 示例使用
async def example_usage():
    """RAG检索器使用示例"""
    
    # 创建检索器
    retriever = create_knowledge_retriever("vector")
    
    # 查询示例
    query_task = {
        "model_name": "bert-base-uncased",
        "task_type": "classification",
        "dataset_name": "imdb"
    }
    
    # 检索相似任务
    similar_tasks = await retriever.retrieve_similar_tasks(query_task)
    print(f"找到 {len(similar_tasks)} 个相似任务")
    
    # 检索解决方案
    problem = "训练损失停滞不下降"
    solutions = await retriever.retrieve_solutions(problem)
    print(f"找到 {len(solutions)} 个解决方案")
    
    # 检索优化建议
    context = {"gpu_usage": 0.95, "training_time": 1200}
    tips = await retriever.retrieve_optimization_tips(context)
    print(f"获得 {len(tips)} 条优化建议")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())