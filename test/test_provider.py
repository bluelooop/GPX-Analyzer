from provider import get_provider_hostname, is_valid_url


def test_get_provider_url():
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


def test_is_valid_url():
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
