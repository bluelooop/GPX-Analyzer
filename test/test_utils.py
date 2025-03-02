import pytest

import utils


def test_haversine():
    # Test case 1: Same points, distance should be 0
    assert utils.haversine(0, 0, 0, 0) == 0

    # Test case 2: Known distance between two points
    assert round(utils.haversine(36.12, -86.67, 33.94, -118.40), 2) == 2886.44

    # Test case 3: Test with points very close to each other
    assert round(utils.haversine(52.5200, 13.4050, 52.5201, 13.4051), 5) == 0.01302


def test_calculate_gradient():
    # Test case 1: Gradient is zero when distance is zero
    assert utils.calculate_gradient(0, 10) == 0

    # Test case 2: Gradient with normal values
    assert utils.calculate_gradient(2, 100) == 5.0

    # Test case 3: Negative elevation difference (downhill)
    assert utils.calculate_gradient(1, -50) == -5.0


def test_deprecated():
    @utils.deprecated(reason="Test function is deprecated")
    def old_function():
        return "This is old"

    # Check if the warning is raised
    with pytest.warns(DeprecationWarning, match="Test function is deprecated"):
        assert old_function() == "This is old"
