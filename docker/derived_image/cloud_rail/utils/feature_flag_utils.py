from typing import Dict


class FeatureFlagUtils:

    @staticmethod
    def to_int(feature_flags: Dict[str, bool], enum_class) -> int:
        total_feature_flags_value = 0
        for feature_flag_name, enabled in feature_flags.items():
            if enabled:
                feature_flag_value = enum_class[feature_flag_name]
                total_feature_flags_value = total_feature_flags_value + feature_flag_value
        return total_feature_flags_value

    @staticmethod
    def from_int(feature_flags: int, enum_class) -> Dict[str, bool]:
        result = {}
        for feature_flag in enum_class:
            if bool(feature_flags & feature_flag.value):
                result[feature_flag.name] = True
        return result
