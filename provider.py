import os
import sys
from typing import Type, TypedDict
from urllib.parse import urlparse

import requests


class GPXProviderError(Exception):
    pass


class RouteGPXProvider:
    """
    A base class for GPX data providers. This class is designed to be extended by specific
    GPX providers to implement their own logic for retrieving GPX data based on a given URI (gpx_uri).
    
    Attributes:
        api_url: The API URL template or endpoint for the specific provider (to be defined in subclasses).
    """
    api_url: None

    @classmethod
    def get_route_gpx_data(cls, gpx_uri: str) -> str:
        """
        A method to be implemented by subclasses to retrieve GPX data from the provider
        based on the provided URI.
    
        Args:
            gpx_uri (str): The URI containing the route information to fetch the GPX data.
    
        Returns:
            str: The GPX data retrieved from the provider.
        """
        pass


class FileRouteGPXProvider(RouteGPXProvider):
    """
    A GPX data provider implementation for local file-based GPX routes.

    This class extends the `RouteGPXProvider` base class and provides functionality
    for retrieving GPX data from local files. It assumes that the provided URI is a 
    valid file path on the local file system.
    """

    @classmethod
    def get_route_gpx_data(cls, gpx_uri: str) -> str:
        try:
            with open(gpx_uri, "r", encoding="utf-8") as f:
                lines = f.readlines()

            return "\n".join(lines)
        except OSError as e:
            raise GPXProviderError(f"File: {e}")


class StravaRouteGPXProvider(RouteGPXProvider):
    """
        A GPX data provider implementation for Strava routes.

        This class extends the `RouteGPXProvider` base class to provide 
        functionality for retrieving GPX route data from Strava using its API. 
        It works by constructing an API request based on a given GPX URI and 
        fetching the corresponding GPX data.
    """
    api_url = "https://www.strava.com/api/v3/routes/{route_id}/export_gpx"

    @classmethod
    def __get_request_headers(cls) -> dict:
        access_key = os.getenv("STRAVA_ACCESS_KEY")

        return {
            "Authorization": f"Bearer {access_key}"
        }

    @classmethod
    def get_route_gpx_data(cls, gpx_uri: str) -> str:
        route_id = gpx_uri.split("/")[-1]
        response = requests.get(cls.api_url.format(route_id=route_id), headers=cls.__get_request_headers())

        if not response.ok:
            raise GPXProviderError(f"Strava: {response.json()['message']}")

        return response.content.decode("utf-8")


__ROUTE_PROVIDERS = {
    "www.strava.com": StravaRouteGPXProvider,
}


def get_provider_hostname(url: str) -> str:
    """
    Extracts and returns the hostname (netloc) from a given URL.
    
    Args:
        url (str): The URL from which to extract the hostname.
    
    Returns:
        str: The extracted hostname (netloc) of the given URL.
    """
    return urlparse(url).netloc


def is_valid_url(url: str) -> bool | None:
    """
    Validates whether a given string is a properly formatted URL.

    This function checks if the provided URL string contains a valid scheme (e.g., 'http' or 'https'),
    network location (e.g., 'www.example.com'), and path. If any of these components are missing,
    the URL is considered invalid.

    Args:
        url (str): The URL to validate.

    Returns:
        bool | None: True if the URL is valid, otherwise False.
    """
    try:
        result = urlparse(url)

        return all([result.scheme, result.netloc, result.path])
    except ValueError:
        pass


def get_gpx_data(uri: str) -> str | None:
    """
    Retrieves GPX data based on the provided URI by delegating the request to the appropriate GPX provider.

    This function determines the source of the GPX data (e.g., Strava or a local file) by extracting the 
    hostname from the URI. It then uses a corresponding GPX data provider class to fetch the data. If no 
    matching provider is found in the predefined list, the function defaults to retrieving the GPX data 
    from a local file.

    Args:
        uri (str): The URI specifying the source of the GPX data. It can be a URL for an online provider 
                   (e.g., Strava) or a local file path.

    Returns:
        str | None: The retrieved GPX data as a string, or None if the retrieval fails or the URI is invalid.
    """
    xml_data = None
    try:
        hostname = get_provider_hostname(uri)
        provider: Type[RouteGPXProvider] = __ROUTE_PROVIDERS.get(hostname, FileRouteGPXProvider)

        xml_data = provider.get_route_gpx_data(uri)
    except GPXProviderError as e:
        print(e, file=sys.stderr)

    return xml_data


class PointElevationError(Exception):
    pass


class Location(TypedDict):
    position: int
    latitude: float
    longitude: float


class LocationElevation(TypedDict):
    latitude: float
    longitude: float
    elevation: float


class PointElevationProvider:
    """
    A base class for retrieving elevation data for a list of geographical locations.

    This class is intended to be extended by specific elevation providers, which
    will implement the logic for querying their respective APIs or data sources
    to obtain elevation information for given latitude/longitude coordinates.

    Attributes:
        api_url (str): The API endpoint URL for the elevation provider. This should
                       be specified in subclasses.
    """
    api_url: None

    @classmethod
    def get_points_elevations(cls, locations: list[Location]) -> list[LocationElevation]:
        """
        Abstract method to retrieve elevations for a list of geographical locations.

        Args:
            locations (list[Location]): A list of dictionaries containing 'latitude'
                                        and 'longitude' keys representing the
                                        geographical locations to query.

        Returns:
            list[LocationElevation]: A list of dictionaries containing 'latitude',
                                      'longitude', and 'elevation' keys for the
                                      queried locations.

        Note:
            This method must be implemented in subclasses.
        """
        pass


class OpenElevationProvider(PointElevationProvider):
    """
    A class for retrieving elevation data using the Open Elevation API.

    This class extends the `PointElevationProvider` base class and provides
    functionality for querying the Open Elevation API to obtain elevation
    data for a list of geographical locations.

    Attributes:
        api_url (str): The API endpoint URL for the Open Elevation service.
    """
    api_url = "https://api.open-elevation.com/api/v1/lookup"

    @classmethod
    def get_points_elevations(cls, locations: list[Location]) -> list[LocationElevation]:
        response = requests.post(cls.api_url, json={"locations": locations})

        if not response.ok:
            raise PointElevationError(f"Open Elevation API: {response.reason}")

        return response.json()["results"]


__POINT_ELEVATION_PROVIDERS = [
    OpenElevationProvider,
]


def get_locations_elevations(locations: list[Location]) -> list[LocationElevation] | None:
    elevations = []
    for provider in __POINT_ELEVATION_PROVIDERS:
        try:
            elevations = provider.get_points_elevations(sorted(locations, key=lambda lo: lo["position"]))

            if elevations:
                break
        except PointElevationError as e:
            print(e, file=sys.stderr)

    return elevations
