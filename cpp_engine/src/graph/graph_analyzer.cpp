#include "spia/graph_analyzer.hpp"
#include <stdexcept>
#include <numeric>

namespace spia {

void GraphAnalyzer::add_node(uint64_t node_id) {
    get_or_create_node(node_id);
}

void GraphAnalyzer::add_edge(uint64_t from, uint64_t to, double weight) {
    size_t from_idx = get_or_create_node(from);
    size_t to_idx = get_or_create_node(to);

    edges_.push_back({from, to, weight});
    nodes_[from_idx].out_edges.push_back(edges_.size() - 1);
    nodes_[to_idx].in_edges.push_back(edges_.size() - 1);
}

void GraphAnalyzer::build_from_edgelist(
    const std::vector<std::pair<uint64_t, uint64_t>>& edges
) {
    for (const auto& [from, to] : edges) {
        add_edge(from, to);
    }
}

size_t GraphAnalyzer::get_or_create_node(uint64_t node_id) {
    auto it = node_map_.find(node_id);
    if (it != node_map_.end()) {
        return it->second;
    }
    size_t idx = nodes_.size();
    node_map_[node_id] = idx;
    nodes_.push_back({node_id, idx, {}, {}});
    return idx;
}

std::vector<std::vector<double>> GraphAnalyzer::build_adjacency_matrix() const {
    size_t n = nodes_.size();
    std::vector<std::vector<double>> matrix(n, std::vector<double>(n, 0.0));

    for (const auto& edge : edges_) {
        size_t from_idx = node_map_.at(edge.from);
        size_t to_idx = node_map_.at(edge.to);
        matrix[from_idx][to_idx] = edge.weight;
    }
    return matrix;
}

std::vector<double> GraphAnalyzer::degree_centrality() const {
    size_t n = nodes_.size();
    if (n <= 1) {
        return std::vector<double>(n, 0.0);
    }

    std::vector<double> centrality(n, 0.0);
    for (size_t i = 0; i < n; ++i) {
        centrality[i] = static_cast<double>(
            nodes_[i].out_edges.size() + nodes_[i].in_edges.size()
        ) / (2.0 * (n - 1));
    }
    return centrality;
}

std::vector<double> GraphAnalyzer::clustering_coefficient() const {
    size_t n = nodes_.size();
    std::vector<double> coefficients(n, 0.0);

    auto adj = build_adjacency_matrix();

    for (size_t i = 0; i < n; ++i) {
        std::vector<size_t> neighbors;
        for (size_t j = 0; j < n; ++j) {
            if (adj[i][j] > 0 || adj[j][i] > 0) {
                neighbors.push_back(j);
            }
        }

        size_t k = neighbors.size();
        if (k < 2) {
            coefficients[i] = 0.0;
            continue;
        }

        size_t edges_between = 0;
        for (size_t a = 0; a < k; ++a) {
            for (size_t b = a + 1; b < k; ++b) {
                if (adj[neighbors[a]][neighbors[b]] > 0 ||
                    adj[neighbors[b]][neighbors[a]] > 0) {
                    edges_between++;
                }
            }
        }

        coefficients[i] = (2.0 * edges_between) / (k * (k - 1));
    }
    return coefficients;
}

std::vector<double> GraphAnalyzer::detect_bot_clusters(
    double centrality_threshold
) const {
    auto centrality = degree_centrality();
    auto clustering = clustering_coefficient();
    size_t n = nodes_.size();

    std::vector<double> bot_scores(n, 0.0);
    for (size_t i = 0; i < n; ++i) {
        bot_scores[i] = (1.0 - clustering[i]) * centrality[i];
    }
    return bot_scores;
}

std::vector<double> GraphAnalyzer::compute_follow_back_ratio() const {
    size_t n = nodes_.size();
    auto adj = build_adjacency_matrix();
    std::vector<double> ratios(n, 0.0);

    for (size_t i = 0; i < n; ++i) {
        double following = std::accumulate(adj[i].begin(), adj[i].end(), 0.0);
        if (following == 0) {
            ratios[i] = 0.0;
            continue;
        }

        double reciprocal = 0.0;
        for (size_t j = 0; j < n; ++j) {
            if (adj[i][j] > 0 && adj[j][i] > 0) {
                reciprocal += 1.0;
            }
        }

        ratios[i] = reciprocal / following;
    }
    return ratios;
}

std::vector<uint64_t> GraphAnalyzer::get_suspicious_nodes(
    double threshold
) const {
    auto scores = detect_bot_clusters();
    std::vector<uint64_t> suspicious;

    for (size_t i = 0; i < scores.size(); ++i) {
        if (scores[i] > threshold) {
            suspicious.push_back(nodes_[i].id);
        }
    }
    return suspicious;
}

} // namespace spia
