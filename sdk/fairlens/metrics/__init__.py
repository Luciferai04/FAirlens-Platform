from .demographic_parity import demographic_parity_difference
from .equalized_odds import equalized_odds_difference
from .disparate_impact import disparate_impact_ratio
from .calibration import calibration_error_per_group
from .theil import theil_index
from .statistical_parity import statistical_parity_difference
from .average_odds import average_odds_difference
from .equal_opportunity import equal_opportunity_difference

ALL_METRICS = {
    "demographic_parity_difference": demographic_parity_difference,
    "equalized_odds_difference": equalized_odds_difference,
    "disparate_impact_ratio": disparate_impact_ratio,
    "calibration_error": calibration_error_per_group,
    "theil_index": theil_index,
    "statistical_parity_difference": statistical_parity_difference,
    "average_odds_difference": average_odds_difference,
    "equal_opportunity_difference": equal_opportunity_difference,
}
