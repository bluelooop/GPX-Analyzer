import os
from urllib.parse import urlparse

import requests


class RouteGPXProvider:
    api_url: None

    @classmethod
    def get_route_gpx_data(cls, gpx_url):
        pass


class StravaRouteGPXProvider(RouteGPXProvider):
    api_url = "https://www.strava.com/api/v3/routes/{route_id}/export_gpx"

    @classmethod
    def __get_request_headers(cls):
        access_key = os.getenv("STRAVA_ACCESS_KEY")

        return {
            "Authorization": f"Bearer {access_key}"
        }

    @classmethod
    def get_route_gpx_data(cls, gpx_url):
        route_id = gpx_url.split("/")[-1]
        response = requests.get(cls.api_url.format(route_id=route_id), headers=cls.__get_request_headers())

        return response.content.decode("utf-8")


__PROVIDERS = {
    "www.strava.com": StravaRouteGPXProvider
}


def get_provider_hostname(url):
    return urlparse(url).netloc


def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc, result.path])
    except ValueError:
        pass


def get_gpx_data(url):
    try:
        hostname = get_provider_hostname(url)
        provider: RouteGPXProvider = __PROVIDERS[hostname]

        return provider.get_route_gpx_data(url)
    except KeyError:
        pass
