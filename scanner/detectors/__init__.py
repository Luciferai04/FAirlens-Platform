from .imbalance import detect_class_imbalance
from .proxy_leakage import detect_proxy_leakage
from .label_bias import detect_label_bias

__all__ = ["detect_class_imbalance", "detect_proxy_leakage", "detect_label_bias"]
