#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
推荐系统离线评估脚本
包含：
1. 训练集/测试集划分
2. 核心评估指标计算（Precision@K/Recall@K/F1@K）
3. 扩展评估指标计算（MAP/NDCG@K/MRR）
4. 完整的离线评估流程
"""

import logging
logger = logging.getLogger(__name__)

import random
import math
import numpy as np
from collections import defaultdict

# 导入推荐系统模块
try:
    from .recommend_4 import (
        HybridMultimodalRecommender,
        load_user_behaviors,
        load_articles,
        MatrixFactorizationRecommender,
        CollaborativeFilteringRecommender,
        DSSMRecommender,
        ContentBasedRecommender
    )
except ImportError as e:
    print(f"导入推荐系统模块失败: {e}")
    print("请确保recommend_4.py文件在当前目录或Python路径中")
    exit(1)


# -----------------------------
# 训练集/测试集划分
# -----------------------------

def split_train_test(behaviors, test_ratio=0.2, seed=42):
    """
    划分训练集和测试集
    
    Args:
        behaviors (dict): 用户行为字典 {user_id: [article_id, ...]}
        test_ratio (float): 测试集比例
        seed (int): 随机种子
    
    Returns:
        tuple: (train_behaviors, test_behaviors)
    """
    random.seed(seed)
    train_behaviors = {}
    test_behaviors = {}
    
    for user_id, items in behaviors.items():
        if len(items) < 2:
            # 行为太少，全部放入训练集
            train_behaviors[user_id] = items
            test_behaviors[user_id] = []
            continue
        
        n_test = max(1, int(len(items) * test_ratio))
        test_items = random.sample(items, n_test)
        train_items = [item for item in items if item not in test_items]
        
        train_behaviors[user_id] = train_items
        test_behaviors[user_id] = test_items
    
    return train_behaviors, test_behaviors


# -----------------------------
# 核心评估指标计算
# -----------------------------

def precision_at_k(recommended, ground_truth, k=30):
    """
    计算Precision@k
    
    Args:
        recommended (list): 推荐的文章ID列表
        ground_truth (list): 用户实际喜欢的文章ID列表
        k (int): 推荐数量
    
    Returns:
        float: Precision@k值
    """
    recommended_k = recommended[:k]
    hits = sum(1 for item in recommended_k if item in ground_truth)
    return hits / k if k > 0 else 0.0

def recall_at_k(recommended, ground_truth, k=30):
    """
    计算Recall@k
    
    Args:
        recommended (list): 推荐的文章ID列表
        ground_truth (list): 用户实际喜欢的文章ID列表
        k (int): 推荐数量
    
    Returns:
        float: Recall@k值
    """
    if not ground_truth:
        return 0.0
    recommended_k = recommended[:k]
    hits = sum(1 for item in recommended_k if item in ground_truth)
    return hits / len(ground_truth)


def f1_at_k(precision, recall):
    """
    计算F1@k
    
    Args:
        precision (float): Precision@k值
        recall (float): Recall@k值
    
    Returns:
        float: F1@k值
    """
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


# -----------------------------
# 扩展评估指标计算
# -----------------------------

def mean_average_precision(recommended, ground_truth):
    """
    计算平均准确率（AP）
    
    Args:
        recommended (list): 推荐的文章ID列表
        ground_truth (list): 用户实际喜欢的文章ID列表
    
    Returns:
        float: AP值
    """
    if not ground_truth:
        return 0.0
    
    hits = 0
    sum_precision = 0.0
    
    for i, item in enumerate(recommended):
        if item in ground_truth:
            hits += 1
            sum_precision += hits / (i + 1)
    
    return sum_precision / len(ground_truth)


def ndcg_at_k(recommended, ground_truth, k=10):
    """
    计算NDCG@k
    
    Args:
        recommended (list): 推荐的文章ID列表
        ground_truth (list): 用户实际喜欢的文章ID列表
        k (int): 推荐数量
    
    Returns:
        float: NDCG@k值
    """
    def dcg(scores):
        return sum(score / math.log2(i + 2) for i, score in enumerate(scores))
    
    recommended_k = recommended[:k]
    ground_truth_set = set(ground_truth)
    
    # 计算DCG
    dcg_scores = [1 if item in ground_truth_set else 0 for item in recommended_k]
    actual_dcg = dcg(dcg_scores)
    
    # 计算理想DCG
    ideal_scores = sorted([1 for _ in ground_truth_set], reverse=True)[:k]
    ideal_dcg = dcg(ideal_scores) if ideal_scores else 0.0
    
    if ideal_dcg == 0:
        return 0.0
    return actual_dcg / ideal_dcg


def mean_reciprocal_rank(recommended, ground_truth):
    """
    计算倒数排名（RR）
    
    Args:
        recommended (list): 推荐的文章ID列表
        ground_truth (list): 用户实际喜欢的文章ID列表
    
    Returns:
        float: RR值
    """
    ground_truth_set = set(ground_truth)
    
    for i, item in enumerate(recommended):
        if item in ground_truth_set:
            return 1.0 / (i + 1)
    
    return 0.0


# -----------------------------
# 完整评估流程
# -----------------------------

def evaluate_recommender(hybrid_rec, test_behaviors, top_k=30, alpha=0.4, delta=0.4, beta=0.1, gamma=0.1):
    print(f"评估推荐器性能，参数: alpha={alpha}, delta={delta}, beta={beta}, gamma={gamma}, top_k={top_k}")
    """
    评估推荐系统性能

    Args:
        hybrid_rec (HybridMultimodalRecommender): 混合推荐器实例
        test_behaviors (dict): 测试集用户行为
        top_k (int): 推荐数量
        alpha (float): 内容推荐的权重
        delta (float): 偏好推荐的权重
        beta (float): 协同过滤推荐的权重
        gamma (float): DSSM多模态推荐的权重

    Returns:
        dict: 评估指标结果
    """
    metrics = {
        'precision@k': [],
        'recall@k': [],
        'f1@k': [],
        'map': [],
        'ndcg@k': [],
        'mrr': []
    }
    
    total_users = len(test_behaviors)
    evaluated_users = 0
    
    for user_id, ground_truth in test_behaviors.items():
        if not ground_truth:
            continue
        
        evaluated_users += 1
        
        try:
            # 获取推荐结果
            results = hybrid_rec.recommend(
                user_id,
                query=None,
                query_image_path=None,
                top_k=top_k,
                alpha=alpha,
                delta=delta,
                beta=beta,
                gamma=gamma,
                cf_method="model_based"
            )
            recommended_ids = [r['article_id'] for r in results]
            print(f"用户 {user_id} 推荐结果: {recommended_ids}")
            
            # 计算指标
            p = precision_at_k(recommended_ids, ground_truth, top_k)
            r = recall_at_k(recommended_ids, ground_truth, top_k)
            f1 = f1_at_k(p, r)
            ap = mean_average_precision(recommended_ids, ground_truth)
            ndcg = ndcg_at_k(recommended_ids, ground_truth, top_k)
            mrr = mean_reciprocal_rank(recommended_ids, ground_truth)
            
            metrics['precision@k'].append(p)
            metrics['recall@k'].append(r)
            metrics['f1@k'].append(f1)
            metrics['map'].append(ap)
            metrics['ndcg@k'].append(ndcg)
            metrics['mrr'].append(mrr)
            
        except Exception as e:
            print(f"评估用户 {user_id} 时出错: {e}")
            continue
        # 打印进度
        if evaluated_users % 10 == 0:
            print(f"已评估 {evaluated_users}/{total_users} 个用户")
    
    # 计算平均值
    avg_metrics = {
        'precision@k': np.mean(metrics['precision@k']) if metrics['precision@k'] else 0.0,
        'recall@k': np.mean(metrics['recall@k']) if metrics['recall@k'] else 0.0,
        'f1@k': np.mean(metrics['f1@k']) if metrics['f1@k'] else 0.0,
        'map': np.mean(metrics['map']) if metrics['map'] else 0.0,
        'ndcg@k': np.mean(metrics['ndcg@k']) if metrics['ndcg@k'] else 0.0,
        'mrr': np.mean(metrics['mrr']) if metrics['mrr'] else 0.0
    }
    
    print(f"\n完成评估，共评估 {evaluated_users} 个用户")
    
    return avg_metrics, evaluated_users


def create_parameter_grid():
    """
    创建参数网格用于遍历测试

    Returns:
        list: 参数组合列表，每个元素为 (alpha, delta, beta, gamma) 元组
    """
    parameter_grid = []

    # 定义各参数的取值范围
    alphas = [0.1, 0.2, 0.3, 0.4, 0.5]  # 内容推荐权重
    deltas = [0.1, 0.2, 0.3, 0.4, 0.5]  # 偏好推荐权重
    betas = [0.1, 0.2, 0.3]             # 协同过滤权重
    gammas = [0.1, 0.2, 0.3]             # DSSM多模态权重

    # 生成所有可能的参数组合
    for alpha in alphas:
        for delta in deltas:
            for beta in betas:
                for gamma in gammas:
                    # 确保权重总和为1.0
                    total = alpha + delta + beta + gamma
                    if abs(total - 1.0) < 0.01:  # 允许小的浮点误差
                        parameter_grid.append((alpha, delta, beta, gamma))

    print(f"生成 {len(parameter_grid)} 组有效参数组合")
    return parameter_grid


def run_offline_evaluation(test_ratio=0.2, top_k=30, seed=42):
    """
    运行完整的离线评估流程
    
    Args:
        test_ratio (float): 测试集比例
        top_k (int): 推荐数量
        seed (int): 随机种子
    
    Returns:
        dict: 评估指标结果
    """
    print("=" * 80)
    print("多模态推荐系统 - 离线评估")
    print("=" * 80)
    
    # 加载数据
    print("\n1. 加载数据...")
    try:
        behaviors = load_user_behaviors()
        articles = load_articles()
    except Exception as e:
        print(f"加载数据失败: {e}")
        return {}
    
    if not behaviors or not articles:
        print("错误：没有加载到数据")
        return {}
    
    print(f"加载到 {len(behaviors)} 个用户，{len(articles)} 篇文章")
    print(f"总交互数: {sum(len(items) for items in behaviors.values())}")
    
    # 划分训练集和测试集
    print("\n2. 划分训练集和测试集...")
    train_behaviors, test_behaviors = split_train_test(behaviors, test_ratio, seed)
    
    # 统计数据分布
    train_count = sum(len(items) for items in train_behaviors.values())
    test_count = sum(len(items) for items in test_behaviors.values())
    
    print(f"训练集: {len(train_behaviors)} 个用户，{train_count} 条交互")
    print(f"测试集: {len(test_behaviors)} 个用户，{test_count} 条交互")
    print(f"测试集比例: {test_ratio:.1%}")
    
    # 初始化并训练推荐器
    print("\n3. 初始化推荐模型...")
    try:
        hybrid_rec = HybridMultimodalRecommender()
        # 替换训练集数据
        hybrid_rec.behaviors = train_behaviors
        hybrid_rec.articles = articles
        
        # 重新初始化各个推荐器以使用新的训练数据
        print("   - 初始化基于内容的推荐模型...")
        hybrid_rec.content_rec = ContentBasedRecommender(articles)
        
        print("   - 初始化协同过滤推荐模型...")
        hybrid_rec.cf_rec = CollaborativeFilteringRecommender(train_behaviors)
        
        print("   - 初始化矩阵分解推荐模型...")
        hybrid_rec.mf_rec = MatrixFactorizationRecommender(train_behaviors)
        
        print("   - 初始化多模态DSSM模型...")
        hybrid_rec.dssm_rec = DSSMRecommender(articles, train_behaviors)
        
    except Exception as e:
        print(f"初始化模型失败: {e}")
        import traceback
        traceback.print_exc()
        return {}
    
    # 评估推荐器
    print("\n4. 评估推荐系统...")
    print(f"将对 {len(test_behaviors)} 个用户进行评估")

    # 创建参数网格
    parameter_grid = create_parameter_grid()

    # 结果保存文件
    result_file = f"test.txt"

    # 遍历所有参数组合
    all_results = []
    for i, (alpha, delta, beta, gamma) in enumerate(parameter_grid, 1):
        print(f"\n{'='*60}")
        print(f"测试第 {i}/{len(parameter_grid)} 组参数:")
        print(f"alpha(内容)={alpha}, delta(偏好)={delta}, beta(CF)={beta}, gamma(DSSM)={gamma}")
        print(f"{'='*60}")

        try:
            # 评估当前参数组合
            metrics, evaluated_users = evaluate_recommender(
                hybrid_rec, test_behaviors, top_k, alpha, delta, beta, gamma
            )

            # 保存结果到列表
            result_entry = {
                'alpha': alpha,
                'delta': delta,
                'beta': beta,
                'gamma': gamma,
                'evaluated_users': evaluated_users,
                'precision': metrics['precision@k'],
                'recall': metrics['recall@k'],
                'f1': metrics['f1@k'],
                'map': metrics['map'],
                'ndcg': metrics['ndcg@k'],
                'mrr': metrics['mrr']
            }
            all_results.append(result_entry)

            # 追加写入文件
            with open(result_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"参数组合 {i}/{len(parameter_grid)}: ")
                f.write(f"alpha={alpha}, delta={delta}, beta={beta}, gamma={gamma}\n")
                f.write(f"{'='*80}\n")
                f.write(f"评估用户数: {evaluated_users}\n")
                f.write(f"推荐数量: {top_k}\n")
                f.write(f"Precision@{top_k}: {metrics['precision@k']:.4f}\n")
                f.write(f"Recall@{top_k}: {metrics['recall@k']:.4f}\n")
                f.write(f"F1@{top_k}: {metrics['f1@k']:.4f}\n")
                f.write(f"MAP: {metrics['map']:.4f}\n")
                f.write(f"NDCG@{top_k}: {metrics['ndcg@k']:.4f}\n")
                f.write(f"MRR: {metrics['mrr']:.4f}\n")

            print(f"✓ 第 {i} 组参数测试完成，结果已保存")

        except Exception as e:
            print(f"✗ 第 {i} 组参数测试失败: {e}")
            with open(result_file, 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*80}\n")
                f.write(f"参数组合 {i}/{len(parameter_grid)}: ")
                f.write(f"alpha={alpha}, delta={delta}, beta={beta}, gamma={gamma}\n")
                f.write(f"{'='*80}\n")
                f.write(f"测试失败: {e}\n")
            continue

    # 找出最佳参数组合
    if all_results:
        best_by_f1 = max(all_results, key=lambda x: x['f1'])
        best_by_ndcg = max(all_results, key=lambda x: x['ndcg'])

        # 保存总结
        with open(result_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*80}\n")
            f.write("参数调优总结\n")
            f.write(f"{'='*80}\n")
            f.write(f"测试完成时间: ")
            try:
                import pandas as pd
                f.write(f"{pd.Timestamp.now()}\n")
            except ImportError:
                f.write(f"(pandas未安装)\n")
            f.write(f"总参数组合数: {len(parameter_grid)}\n")
            f.write(f"成功测试组合数: {len(all_results)}\n\n")

            f.write("最佳参数组合 (按F1分数):\n")
            f.write(f"  alpha={best_by_f1['alpha']}, delta={best_by_f1['delta']}, ")
            f.write(f"beta={best_by_f1['beta']}, gamma={best_by_f1['gamma']}\n")
            f.write(f"  F1@{top_k}: {best_by_f1['f1']:.4f}\n")
            f.write(f"  NDCG@{top_k}: {best_by_f1['ndcg']:.4f}\n\n")

            f.write("最佳参数组合 (按NDCG分数):\n")
            f.write(f"  alpha={best_by_ndcg['alpha']}, delta={best_by_ndcg['delta']}, ")
            f.write(f"beta={best_by_ndcg['beta']}, gamma={best_by_ndcg['gamma']}\n")
            f.write(f"  F1@{top_k}: {best_by_ndcg['f1']:.4f}\n")
            f.write(f"  NDCG@{top_k}: {best_by_ndcg['ndcg']:.4f}\n")

        print(f"\n{'='*80}")
        print("参数调优完成!")
        print(f"最佳参数组合 (F1): alpha={best_by_f1['alpha']}, delta={best_by_f1['delta']}, beta={best_by_f1['beta']}, gamma={best_by_f1['gamma']}")
        print(f"最佳F1分数: {best_by_f1['f1']:.4f}")
        print(f"结果已保存到: {result_file}")
        print(f"{'='*80}")

    return all_results


# -----------------------------
# 主函数
# -----------------------------

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="多模态推荐系统离线评估")
    parser.add_argument('--test-ratio', type=float, default=0.2,
                       help='测试集比例 (default: 0.2)')
    parser.add_argument('--top-k', type=int, default=10,
                       help='推荐数量 (default: 10)')
    parser.add_argument('--seed', type=int, default=42,
                       help='随机种子 (default: 42)')
    
    args = parser.parse_args()
    
    print(f"评估参数:")
    print(f"  测试集比例: {args.test_ratio:.1%}")
    print(f"  推荐数量: {args.top_k}")
    print(f"  随机种子: {args.seed}")
    print()
    
    # 运行评估
    results = run_offline_evaluation(
        test_ratio=args.test_ratio,
        top_k=args.top_k,
        seed=args.seed
    )

    if results:
        print("\n参数调优评估完成!")
    else:
        print("\n评估失败!")
        exit(1)


if __name__ == "__main__":
    main()
