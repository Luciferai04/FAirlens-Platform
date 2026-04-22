"""
Tests for Page-Hinkley drift detector.
Verifies drift detection fires within 20 samples of injection point.
"""
import pytest
from monitor.drift.page_hinkley import PageHinkleyDetector


class TestPageHinkleyDetector:
    def test_no_drift_on_stable_stream(self):
        """Stable stream at 0.5 should not trigger drift."""
        detector = PageHinkleyDetector(delta=0.005, threshold=50)
        for _ in range(200):
            assert detector.update(0.5) is False

    def test_detects_drift_on_shift(self):
        """Drift should be detected when mean shifts from 0.5 to 0.9."""
        detector = PageHinkleyDetector(delta=0.005, threshold=50)
        # Stable phase
        for _ in range(100):
            detector.update(0.5)
        # Inject drift at position 100
        drift_position = None
        for i in range(200):
            if detector.update(0.9):
                drift_position = i
                break
        assert drift_position is not None, "Drift was never detected"
        assert drift_position < 20, f"Drift detected too late at position {drift_position}"

    def test_reset_clears_state(self):
        detector = PageHinkleyDetector()
        for _ in range(50):
            detector.update(0.5)
        assert detector.n == 50
        detector.reset()
        assert detector.n == 0
        assert detector.sum == 0.0
        assert detector.min_sum == float("inf")

    def test_equity_score_starts_at_one(self):
        detector = PageHinkleyDetector()
        assert detector.current_equity_score() == 1.0
        for _ in range(5):
            detector.update(0.5)
        assert detector.current_equity_score() == 1.0  # < 10 samples

    def test_equity_score_decreases_with_drift(self):
        detector = PageHinkleyDetector(delta=0.005, threshold=50)
        for _ in range(100):
            detector.update(0.5)
        score_before = detector.current_equity_score()
        for _ in range(100):
            detector.update(0.9)
        score_after = detector.current_equity_score()
        assert score_after < score_before

    def test_sensitivity_with_different_thresholds(self):
        """Lower threshold = faster detection."""
        fast = PageHinkleyDetector(delta=0.005, threshold=10)
        slow = PageHinkleyDetector(delta=0.005, threshold=100)

        fast_detection = None
        slow_detection = None

        for i in range(300):
            val = 0.5 if i < 100 else 0.9
            if fast.update(val) and fast_detection is None:
                fast_detection = i - 100
            if slow.update(val) and slow_detection is None:
                slow_detection = i - 100

        assert fast_detection is not None
        if slow_detection is not None:
            assert fast_detection <= slow_detection
