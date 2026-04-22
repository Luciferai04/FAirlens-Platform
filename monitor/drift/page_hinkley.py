"""
Page-Hinkley sequential change point detector.
Detects sustained shifts in the mean of a metric stream (two-sided).

Reference: Mouss et al., "Test of Page-Hinkley, an approach for fault detection
in an agro-alimentary production system." IFAC 2004.

Parameters:
    delta: Minimum magnitude of change to detect. Smaller values make the
           detector more sensitive to small shifts. Default: 0.005
    threshold: Cumulative sum threshold for drift declaration. Smaller values
               make detection faster but increase false positives. Default: 50
    alpha: Exponential smoothing factor for running mean estimate. Values
           closer to 1.0 weight historical data more heavily. Default: 0.9999
"""


class PageHinkleyDetector:
    """
    Two-sided Page-Hinkley test for detecting changes in the mean of a stream.

    The detector maintains two cumulative sums — one for upward shifts and one
    for downward shifts. When either exceeds the threshold, drift is declared.
    """

    def __init__(self, delta: float = 0.005, threshold: float = 50,
                 alpha: float = 0.9999):
        self.delta = delta
        self.threshold = threshold
        self.alpha = alpha
        self._reset()

    def _reset(self):
        """Reset internal state."""
        self.n = 0
        self.x_sum = 0.0
        self.mean = 0.0
        # Upward shift tracking
        self.sum_up = 0.0
        self.min_sum_up = float("inf")
        # Downward shift tracking
        self.sum_down = 0.0
        self.max_sum_down = float("-inf")
        self._window = []

    def reset(self):
        """Public reset method — clears all accumulated state."""
        self._reset()

    def update(self, value: float) -> bool:
        """
        Update detector with a new observation.

        Args:
            value: New observation value (e.g., positive prediction rate)

        Returns:
            True if drift is detected (cumulative deviation exceeds threshold)
        """
        self.n += 1
        self._window.append(value)
        if len(self._window) > 500:
            self._window.pop(0)

        # Initialize mean from first observation to prevent cold-start drift
        if self.n == 1:
            self.mean = value
            return False

        # Update running mean
        old_mean = self.mean
        self.mean = self.alpha * self.mean + (1 - self.alpha) * value

        # Upward shift detector (detects increase in mean)
        self.sum_up += value - old_mean - self.delta
        self.min_sum_up = min(self.min_sum_up, self.sum_up)
        up_drift = (self.sum_up - self.min_sum_up) > self.threshold

        # Downward shift detector (detects decrease in mean)
        self.sum_down += old_mean - value - self.delta
        self.max_sum_down = max(self.max_sum_down, self.sum_down)
        down_drift = (self.sum_down - self.max_sum_down) < -self.threshold

        # Alternative: also check max deviation for downward
        self.min_sum_down = getattr(self, 'min_sum_down', float("inf"))
        self.min_sum_down = min(self.min_sum_down, self.sum_down)
        down_drift2 = (self.sum_down - self.min_sum_down) > self.threshold

        return up_drift or down_drift2

    def current_equity_score(self) -> float:
        """
        Equity score: 1.0 = perfect (no drift), lower = more drift detected.
        Clamped to [0, 1].
        """
        if self.n < 10:
            return 1.0
        magnitude = max(
            self.sum_up - self.min_sum_up,
            self.sum_down - getattr(self, 'min_sum_down', 0),
        )
        return max(0.0, min(1.0, 1.0 - (magnitude / (self.threshold * 2))))

    @property
    def drift_magnitude(self) -> float:
        """Current drift magnitude (max of up and down deviations)."""
        return max(
            self.sum_up - self.min_sum_up,
            self.sum_down - getattr(self, 'min_sum_down', 0),
        )

