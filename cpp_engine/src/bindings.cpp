#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "spia/graph_analyzer.hpp"
#include "spia/feature_hasher.hpp"

namespace py = pybind11;

PYBIND11_MODULE(spia_engine, m) {
    m.doc() = "Spia C++ Engine - High-performance bot detection module";

    py::class_<spia::GraphAnalyzer>(m, "GraphAnalyzer")
        .def(py::init<>())
        .def("add_node", &spia::GraphAnalyzer::add_node)
        .def("add_edge", &spia::GraphAnalyzer::add_edge)
        .def("build_from_edgelist", &spia::GraphAnalyzer::build_from_edgelist)
        .def("degree_centrality", &spia::GraphAnalyzer::degree_centrality)
        .def("clustering_coefficient", &spia::GraphAnalyzer::clustering_coefficient)
        .def("detect_bot_clusters", &spia::GraphAnalyzer::detect_bot_clusters,
             py::arg("centrality_threshold") = 0.5)
        .def("compute_follow_back_ratio", &spia::GraphAnalyzer::compute_follow_back_ratio)
        .def("get_suspicious_nodes", &spia::GraphAnalyzer::get_suspicious_nodes,
             py::arg("threshold") = 0.6)
        .def("node_count", &spia::GraphAnalyzer::node_count)
        .def("edge_count", &spia::GraphAnalyzer::edge_count);

    py::class_<spia::FeatureHasher>(m, "FeatureHasher")
        .def(py::init<size_t>(), py::arg("num_features") = 1024)
        .def("hash_feature", &spia::FeatureHasher::hash_feature)
        .def("hash_feature_vector", &spia::FeatureHasher::hash_feature_vector)
        .def("normalize_features", &spia::FeatureHasher::normalize_features)
        .def("compute_entropy", &spia::FeatureHasher::compute_entropy)
        .def("compute_digit_ratio", &spia::FeatureHasher::compute_digit_ratio)
        .def("compute_statistical_features",
             &spia::FeatureHasher::compute_statistical_features);
}
