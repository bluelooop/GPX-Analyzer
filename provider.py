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
        name (str): The name of the provider (to be defined in subclasses).
        api_url: The API URL template or endpoint for the specific provider (to be defined in subclasses).
    """
    name: str
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
    name = "Local File"

    @classmethod
    def get_route_gpx_data(cls, gpx_uri: str) -> str:
        try:
            with open(gpx_uri, "r", encoding="utf-8") as f:
                lines = f.readlines()

            return "\n".join(lines)
        except OSError as e:
            raise GPXProviderError(f"{cls.name}: {e}")


class StravaRouteGPXProvider(RouteGPXProvider):
    """
        A GPX data provider implementation for Strava routes.

        This class extends the `RouteGPXProvider` base class to provide 
        functionality for retrieving GPX route data from Strava using its API. 
        It works by constructing an API request based on a given GPX URI and 
        fetching the corresponding GPX data.
    """
    name = "Strava"
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
            raise GPXProviderError(f"{cls.name}: {response.json()['message']}")

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

        print(f"Retrieving GPX data using {provider.name}...")
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
        name (str): The name of the elevation provider. This should be specified in subclasses.
    """
    name: str
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
        name (str): The name of the elevation provider.
    """
    name = "Open Elevation API"
    api_url = "https://api.open-elevation.com/api/v1/lookup"

    @classmethod
    def get_points_elevations(cls, locations: list[Location]) -> list[LocationElevation]:
        response = requests.post(cls.api_url, json={"locations": locations})

        if not response.ok:
            raise PointElevationError(f"{cls.name}: {response.reason}")

        return response.json()["results"]


class GoogleElevationProvider(PointElevationProvider):
    """
    A class for retrieving elevation data using the Google Elevation API.

    This class extends the `PointElevationProvider` base class and implements
    the logic required to query the Google Elevation API. It fetches elevation
    data for a list of geographical locations (latitude and longitude).

    Attributes:
        api_url (str): The API endpoint URL for the Google Elevation service.
        name (str): The name of the elevation provider.
        max_location_per_request (int): The maximum number of locations that
                                        can be included in a single request.
    """
    name = "Google Elevation API"
    api_url = "https://maps.googleapis.com/maps/api/elevation/json"

    # Reference: https://developers.google.com/maps/documentation/elevation/requests-elevation#Paths
    max_location_per_request = 200

    @classmethod
    def __get_locations_per_requests(cls, locations: list[Location]) -> list[list[Location]]:
        """
        Splits a list of locations into smaller batches to adhere to the API's 
        maximum location limit per request.

        Args:
            locations (list[Location]): A list of dictionaries containing 'latitude'
                                        and 'longitude' keys.

        Returns:
            list[list[Location]]: A list of smaller lists, each containing
                                  up to 'max_location_per_request' locations.
        """
        pages = len(locations) // cls.max_location_per_request + 1
        locations_per_request = []

        for page in range(pages):
            locations_per_request.append(
                locations[page * cls.max_location_per_request: (page + 1) * cls.max_location_per_request]
            )

        return locations_per_request

    @classmethod
    def __get_locations_elevations(cls, locations: list[Location]) -> list[LocationElevation]:
        """
        Sends a request to the Google Elevation API to fetch elevation data
        for a given list of locations.

        Args:
            locations (list[Location]): A list of dictionaries containing 'latitude'
                                        and 'longitude' keys.

        Returns:
            list[LocationElevation]: A list of dictionaries containing 'latitude',
                                      'longitude', and 'elevation' keys.

        Raises:
            PointElevationError: If the API request fails or returns an error.
        """
        locations_data = "|".join([f"{lo['latitude']},{lo['longitude']}" for lo in locations])

        response = requests.get(cls.api_url, params={
            "locations": locations_data,
            "key": os.getenv("GOOGLE_ELEVATION_API_KEY")
        })

        if not response.ok:
            raise PointElevationError(f"{cls.name}: {response.reason}")

        return [
            {"latitude": p["location"]["lat"], "longitude": p["location"]["lng"], "elevation": p["elevation"]}
            for p in response.json()["results"]
        ]

    @classmethod
    def get_points_elevations(cls, locations: list[Location]) -> list[LocationElevation]:
        locations_per_request = cls.__get_locations_per_requests(locations)
        location_results = []
        exception = None

        for locations in locations_per_request:
            try:
                location_results.extend(cls.__get_locations_elevations(locations))
            except PointElevationError as e:
                exception = e

        if exception:
            raise exception

        return location_results


__POINT_ELEVATION_PROVIDERS: list[Type[PointElevationProvider]] = [
    OpenElevationProvider,
]


def __setting_providers():
    if os.getenv("GOOGLE_ELEVATION_API_KEY"):
        __POINT_ELEVATION_PROVIDERS.insert(0, GoogleElevationProvider)


def get_locations_elevations(locations: list[Location]) -> list[LocationElevation] | None:
    """
    Retrieves elevation data for a list of geographical locations using available elevation providers.

    This function attempts to fetch elevation information for the given locations by iterating through
    a predefined list of elevation providers. Each provider is queried in turn until a successful
    response with elevation data is obtained or all providers are exhausted.

    Args:
        locations (list[Location]): A list of dictionaries, each containing the keys:
            - 'position' (int): The position or index of the location in the list.
            - 'latitude' (float): The latitude of the location.
            - 'longitude' (float): The longitude of the location.

    Returns:
        list[LocationElevation] | None: A list of dictionaries, each containing the keys:
            - 'latitude' (float): The latitude of the location.
            - 'longitude' (float): The longitude of the location.
            - 'elevation' (float): The retrieved elevation for the location.
        Returns None if no elevation data is retrieved from any provider.

    Raises:
        None: Exceptions raised by providers are caught and logged to STDERR.

    Notes:
        - The locations are sorted by their 'position' key before querying the providers, ensuring
          that the order of the input list is preserved in the results.
        - If fetching elevation data fails for all providers, the function returns None.
    """
    elevations = []

    __setting_providers()

    for provider in __POINT_ELEVATION_PROVIDERS:  # type: PointElevationProvider
        try:
            print(f"{provider.name}: Trying to get points elevations...")
            elevations = provider.get_points_elevations(sorted(locations, key=lambda lo: lo["position"]))

            if elevations:
                print(f"{provider.name}: Points elevations retrieved successfully!")
                break
        except PointElevationError as e:
            print(e, file=sys.stderr)

    return elevations
