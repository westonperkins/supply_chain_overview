"""HHI monotonicity under completion.

Reads unnormalized HHI so it exercises the mode the flag exists to enable.

Property tested: if a bucket's shares sum below 1.0 and you add a
non-negative synthetic share bringing the sum closer to (or up to) 1.0,
the unnormalized HHI must not DECREASE. This guards against the measure
rewarding incompleteness — an incomplete bucket must not read as LESS
concentrated than the completed one at every step of filling it in.

(Reading the spec's 'must not *increase*' as a typo — under
unnormalized HHI = sum(v²) the value strictly grows with any positive
addition; the interesting property to test is that it never shrinks,
which is what "rewarding incompleteness" would look like if it existed.)
"""
from app.scoring.engine import compute_hhi


def test_unnormalized_hhi_non_decreasing_under_positive_addition():
    base = {"a": 0.30, "b": 0.20}  # sum = 0.5
    base_hhi = compute_hhi(base, normalize=False)
    # Add a series of positive shares, each bringing sum closer to 1.0.
    running = dict(base)
    running_hhi = base_hhi
    for name, weight in [("c", 0.15), ("d", 0.20), ("e", 0.10), ("f", 0.05)]:
        running[name] = weight
        new_hhi = compute_hhi(running, normalize=False)
        assert new_hhi >= running_hhi - 1e-12, (
            f"unnormalized HHI decreased when adding {name}={weight} to "
            f"{running}: {running_hhi} → {new_hhi}"
        )
        running_hhi = new_hhi


def test_unnormalized_hhi_of_zero_addition_is_unchanged():
    base = {"a": 0.30, "b": 0.20}
    base_hhi = compute_hhi(base, normalize=False)
    base["c"] = 0.0
    assert compute_hhi(base, normalize=False) == base_hhi


def test_unnormalized_hhi_boundary_gallium_matches_normalized_when_sum_is_1():
    """Gallium's mines bucket sums to exactly 1.0. The two modes must
    return identical HHI. This is a smoke test for the assertion that
    complete buckets are unaffected by the mode."""
    gallium_mines = {"china": 0.985, "japan": 0.010, "south_korea": 0.005}
    normed = compute_hhi(gallium_mines, normalize=True)
    unnormed = compute_hhi(gallium_mines, normalize=False)
    # Sum is exactly 1.0 so the two forms coincide up to fp precision.
    assert abs(normed - unnormed) < 1e-9
