from scripts.aggregate_reproducible_results import METRIC_KEYS, normalize_metric_block


def test_normalize_metric_block_preserves_null_std_for_single_run():
    source = {
        key: {"mean": 0.5, "std": None, "per_seed": {"42": 0.5}}
        for key in METRIC_KEYS
    }
    normalized = normalize_metric_block(source)
    assert all(normalized[key]["std"] is None for key in METRIC_KEYS)
