#pragma once

#include <vector>
#include <string>
#include <cstdint>
#include <array>
#include <functional>

namespace spia {

class FeatureHasher {
public:
    FeatureHasher(size_t num_features = 1024);

    uint64_t hash_feature(const std::string& feature_name, double value) const;
    std::vector<uint64_t> hash_feature_vector(
        const std::vector<double>& features,
        const std::vector<std::string>& feature_names
    ) const;

    std::vector<double> normalize_features(const std::vector<double>& features) const;
    double compute_entropy(const std::string& text) const;
    double compute_digit_ratio(const std::string& text) const;

    std::vector<double> compute_statistical_features(
        const std::vector<double>& time_series
    ) const;

private:
    size_t num_features_;
    uint64_t mix_bits(uint64_t x) const;
};

} // namespace spia
