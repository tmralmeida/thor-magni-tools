import numpy as np

AVAILABLE_SCENARIOS = ["Scenario", "eth", "univ", "zara1", "zara2", "hotel"]


def log_metrics(logger, metrics):
    for metric_name, metric_value in metrics.items():
        metric_value = np.array(metric_value)
        if metric_name == "perception_noise":
            metric_value = np.absolute(metric_value)
        logger.debug(
            "%s: %1.2f+-%1.2f",
            metric_name,
            metric_value.mean(),
            metric_value.std(),
        )
        if metric_name == "path_efficiency":
            logger.debug("Number of tracklets in the benchmark: %d", len(metric_value))

