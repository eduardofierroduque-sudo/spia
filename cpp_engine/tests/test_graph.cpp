#include <iostream>
#include <cassert>
#include <vector>
#include "spia/graph_analyzer.hpp"
#include "spia/feature_hasher.hpp"

void test_graph_analyzer() {
    spia::GraphAnalyzer graph;

    std::vector<std::pair<uint64_t, uint64_t>> edges = {
        {1, 2}, {1, 3}, {2, 3}, {2, 4},
        {3, 1}, {3, 4}, {4, 5}, {5, 1},
    };
    graph.build_from_edgelist(edges);

    std::cout << "Nodes: " << graph.node_count() << std::endl;
    std::cout << "Edges: " << graph.edge_count() << std::endl;

    assert(graph.node_count() == 5);
    assert(graph.edge_count() == 8);

    auto centrality = graph.degree_centrality();
    std::cout << "Degree centrality size: " << centrality.size() << std::endl;

    auto clustering = graph.clustering_coefficient();
    std::cout << "Clustering coefficient size: " << clustering.size() << std::endl;

    auto bot_scores = graph.detect_bot_clusters();
    std::cout << "Bot scores size: " << bot_scores.size() << std::endl;

    auto suspicious = graph.get_suspicious_nodes(0.4);
    std::cout << "Suspicious nodes: " << suspicious.size() << std::endl;

    auto fb_ratio = graph.compute_follow_back_ratio();
    std::cout << "Follow-back ratio size: " << fb_ratio.size() << std::endl;

    std::cout << "GraphAnalyzer tests passed!" << std::endl;
}

void test_feature_hasher() {
    spia::FeatureHasher hasher(2048);

    uint64_t h1 = hasher.hash_feature("follow_ratio", 5.0);
    uint64_t h2 = hasher.hash_feature("follow_ratio", 5.0);
    assert(h1 == h2);

    double entropy = hasher.compute_entropy("abc123xyz");
    std::cout << "Entropy: " << entropy << std::endl;

    double digit_ratio = hasher.compute_digit_ratio("user12345");
    std::cout << "Digit ratio: " << digit_ratio << std::endl;
    assert(digit_ratio > 0.4);

    std::vector<double> features = {1.0, 2.0, 3.0, 4.0, 5.0};
    std::vector<std::string> names = {"f1", "f2", "f3", "f4", "f5"};
    auto hashes = hasher.hash_feature_vector(features, names);
    assert(hashes.size() == 5);

    auto normalized = hasher.normalize_features(features);
    assert(normalized.size() == 5);

    std::vector<double> ts = {1.0, 2.0, 3.0, 4.0, 5.0, 4.0, 3.0, 2.0, 1.0};
    auto stats = hasher.compute_statistical_features(ts);
    assert(stats.size() == 4);

    std::cout << "FeatureHasher tests passed!" << std::endl;
}

int main() {
    test_graph_analyzer();
    test_feature_hasher();
    std::cout << "All tests passed!" << std::endl;
    return 0;
}
