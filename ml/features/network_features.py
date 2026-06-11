import math
import numpy as np
from typing import Optional


class NetworkFeatureExtractor:
    @staticmethod
    def compute_degree_centrality(adj_matrix: np.ndarray) -> np.ndarray:
        n = adj_matrix.shape[0]
        if n == 0:
            return np.array([])
        return adj_matrix.sum(axis=1) / (n - 1) if n > 1 else np.zeros(n)

    @staticmethod
    def compute_clustering_coefficient(adj_matrix: np.ndarray) -> np.ndarray:
        n = adj_matrix.shape[0]
        coefficients = np.zeros(n)
        for i in range(n):
            neighbors = np.where(adj_matrix[i] > 0)[0]
            k = len(neighbors)
            if k < 2:
                coefficients[i] = 0.0
                continue
            subgraph = adj_matrix[np.ix_(neighbors, neighbors)]
            edges = np.sum(subgraph) / 2
            coefficients[i] = (2 * edges) / (k * (k - 1))
        return coefficients

    @staticmethod
    def detect_bot_clusters(
        adj_matrix: np.ndarray,
        centrality_threshold: float = 0.5,
    ) -> np.ndarray:
        centrality = NetworkFeatureExtractor.compute_degree_centrality(adj_matrix)
        clustering = NetworkFeatureExtractor.compute_clustering_coefficient(adj_matrix)
        bot_score = (1 - clustering) * centrality
        return bot_score

    @staticmethod
    def compute_follow_back_ratio(
        adj_matrix: np.ndarray,
    ) -> np.ndarray:
        n = adj_matrix.shape[0]
        ratios = np.zeros(n)
        for i in range(n):
            followers = np.sum(adj_matrix[:, i])
            following = np.sum(adj_matrix[i, :])
            reciprocal = np.sum(adj_matrix[i, :] * adj_matrix[:, i])
            ratios[i] = reciprocal / max(following, 1) if following > 0 else 0.0
        return ratios
