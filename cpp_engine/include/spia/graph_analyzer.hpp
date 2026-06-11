#pragma once

#include <vector>
#include <cstdint>
#include <string>
#include <unordered_map>
#include <algorithm>
#include <numeric>
#include <cmath>

namespace spia {

class GraphAnalyzer {
public:
    GraphAnalyzer() = default;

    void add_node(uint64_t node_id);
    void add_edge(uint64_t from, uint64_t to, double weight = 1.0);
    void build_from_edgelist(const std::vector<std::pair<uint64_t, uint64_t>>& edges);

    std::vector<double> degree_centrality() const;
    std::vector<double> clustering_coefficient() const;

    std::vector<double> detect_bot_clusters(double centrality_threshold = 0.5) const;
    std::vector<double> compute_follow_back_ratio() const;

    std::vector<uint64_t> get_suspicious_nodes(double threshold = 0.6) const;

    size_t node_count() const { return node_map_.size(); }
    size_t edge_count() const { return edges_.size(); }

private:
    struct Node {
        uint64_t id;
        size_t index;
        std::vector<size_t> out_edges;
        std::vector<size_t> in_edges;
    };

    struct Edge {
        uint64_t from;
        uint64_t to;
        double weight;
    };

    std::vector<Node> nodes_;
    std::vector<Edge> edges_;
    std::unordered_map<uint64_t, size_t> node_map_;

    size_t get_or_create_node(uint64_t node_id);
    std::vector<std::vector<double>> build_adjacency_matrix() const;
};

} // namespace spia
