#include "spia/feature_hasher.hpp"
#include <cmath>
#include <unordered_map>
#include <algorithm>
#include <numeric>
#include <cassert>

namespace spia {

FeatureHasher::FeatureHasher(size_t num_features)
    : num_features_(num_features) {}

uint64_t FeatureHasher::mix_bits(uint64_t x) const {
    x ^= x >> 33;
    x *= 0xff51afd7ed558ccdULL;
    x ^= x >> 33;
    x *= 0xc4ceb9fe1a85ec53ULL;
    x ^= x >> 33;
    return x;
}

uint64_t FeatureHasher::hash_feature(
    const std::string& feature_name,
    double value
) const {
    std::hash<std::string> str_hash;
    std::hash<double> double_hash;

    uint64_t h = str_hash(feature_name);
    h = mix_bits(h ^ double_hash(value));
    return h % num_features_;
}

std::vector<uint64_t> FeatureHasher::hash_feature_vector(
    const std::vector<double>& features,
    const std::vector<std::string>& feature_names
) const {
    assert(features.size() == feature_names.size());

    std::vector<uint64_t> hashes;
    hashes.reserve(features.size());

    for (size_t i = 0; i < features.size(); ++i) {
        hashes.push_back(hash_feature(feature_names[i], features[i]));
    }
    return hashes;
}

std::vector<double> FeatureHasher::normalize_features(
    const std::vector<double>& features
) const {
    if (features.empty()) return {};

    double sum = 0.0;
    double sq_sum = 0.0;
    size_t n = features.size();

    for (double v : features) {
        sum += v;
        sq_sum += v * v;
    }

    double mean = sum / n;
    double variance = (sq_sum / n) - (mean * mean);
    double std_dev = std::sqrt(std::max(variance, 1e-10));

    std::vector<double> normalized;
    normalized.reserve(n);
    for (double v : features) {
        normalized.push_back((v - mean) / std_dev);
    }
    return normalized;
}

double FeatureHasher::compute_entropy(const std::string& text) const {
    if (text.empty()) return 0.0;

    std::unordered_map<char, size_t> freq;
    for (char c : text) {
        freq[c]++;
    }

    double entropy = 0.0;
    double n = static_cast<double>(text.size());
    for (const auto& [ch, count] : freq) {
        double p = count / n;
        entropy -= p * std::log2(p);
    }
    return entropy;
}

double FeatureHasher::compute_digit_ratio(const std::string& text) const {
    if (text.empty()) return 0.0;

    size_t digits = 0;
    for (char c : text) {
        if (c >= '0' && c <= '9') {
            digits++;
        }
    }
    return static_cast<double>(digits) / text.size();
}

std::vector<double> FeatureHasher::compute_statistical_features(
    const std::vector<double>& time_series
) const {
    if (time_series.empty()) {
        return {0.0, 0.0, 0.0, 0.0};
    }

    size_t n = time_series.size();
    double mean = std::accumulate(time_series.begin(), time_series.end(), 0.0) / n;

    double variance = 0.0;
    for (double v : time_series) {
        variance += (v - mean) * (v - mean);
    }
    variance /= n;
    double std_dev = std::sqrt(variance);

    double skewness = 0.0;
    double kurtosis = 0.0;
    for (double v : time_series) {
        double diff = (v - mean) / std::max(std_dev, 1e-10);
        skewness += diff * diff * diff;
        kurtosis += diff * diff * diff * diff;
    }
    skewness /= n;
    kurtosis = (kurtosis / n) - 3.0;

    return {mean, std_dev, skewness, kurtosis};
}

} // namespace spia
