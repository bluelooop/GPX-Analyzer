from unittest.mock import patch

from provider import get_locations_elevations, Location, LocationElevation, PointElevationError
from provider import get_provider_hostname, is_valid_url


class TestRouteProvider:

    def test_get_provider_url(self):
        # Define test cases as input URLs with expected results
        test_cases = [
            ("https://www.strava.com/activities/123456", "www.strava.com"),
            ("https://maps.google.com/something", "maps.google.com"),
            ("http://example.com/test", "example.com"),
            ("ftp://files.example.com/resource", "files.example.com"),
            ("invalid_url", ""),  # This will handle cases where the URL is invalid but parsed netloc is empty
        ]

        for url, expected in test_cases:
            # Use get_provider_name and assert that the result matches the expected netloc
            assert get_provider_hostname(url) == expected

    def test_is_valid_url(self):
        # Define test cases with input URLs and their expected validity
        test_cases = [
            ("https://www.strava.com/activities/123456", True),  # Valid HTTPS URL
            ("http://example.com/test", True),  # Valid HTTP URL
            ("ftp://files.example.com/resource", True),  # Valid FTP URL
            ("www.example.com", False),  # Missing scheme
            ("example.com", False),  # Missing scheme
            ("not-a-valid-url", False),  # Invalid URL
            ("https://", False),  # Missing netloc
            ("", False),  # Empty string
            (None, False),  # None as input
        ]

        for url, expected in test_cases:
            # Use is_valid_url and assert if the result matches the expected validity
            assert is_valid_url(url) == expected


class TestLocationElevationProvider:

    def test_get_location_elevations_success(self):
        # Mock input
        locations = [Location(latitude=10.0, longitude=20.0, position=1)]

        # Mock return value for locations with elevations
        mock_elevations = [LocationElevation(latitude=10.0, longitude=20.0, elevation=100.0)]

        # Patch the OpenElevationProvider's method
        with patch("provider.OpenElevationProvider.get_points_elevations", return_value=mock_elevations) as mock_method:
            result = get_locations_elevations(locations)

            # Assert that the mocked method was called
            mock_method.assert_called_once_with(locations)

            # Assert that the result matches the mocked elevations
            assert result == mock_elevations

    def test_get_location_elevations_no_elevation_found(self):
        # Mock input
        locations = [Location(latitude=10.0, longitude=20.0, position=1)]

        # Simulate no elevation data found by returning an empty list
        with patch("provider.OpenElevationProvider.get_points_elevations", return_value=[]) as mock_method:
            result = get_locations_elevations(locations)

            # Assert that the mocked method was called
            mock_method.assert_called_once_with(locations)

            # Assert that the result is an empty list
            assert result == []

    def test_get_location_elevations_exception_handling(self, capfd):
        # Mock input
        locations = [Location(latitude=10.0, longitude=20.0, position=1)]

        # Simulate an exception being raised
        with patch("provider.OpenElevationProvider.get_points_elevations",
                   side_effect=PointElevationError("Test exception")) as mock_method:
            result = get_locations_elevations(locations)

            # Assert that the mocked method was called
            mock_method.assert_called_once_with(locations)

            # Assert that the result is None due to the exception
            assert result == []

            # Capture stderr output
            captured = capfd.readouterr()
            assert "Test exception" in captured.err
