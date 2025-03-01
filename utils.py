import math


def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points on the Earth's surface.

    Parameters:
        lat1 (float): Latitude of the first point in decimal degrees.
        lon1 (float): Longitude of the first point in decimal degrees.
        lat2 (float): Latitude of the second point in decimal degrees.
        lon2 (float): Longitude of the second point in decimal degrees.

    Returns:
        float: The distance between the two points in kilometers.
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    diff_longitude = lon2 - lon1
    diff_latitude = lat2 - lat1
    a = math.sin(diff_latitude / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(diff_longitude / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return c * r


def calculate_gradient(distance, elevation_diff):
    """
    Calculate the gradient of a slope as a percentage.

    Parameters:
        distance (float): Horizontal distance in kilometers.
        elevation_diff (float): Difference in elevation in meters.

    Returns:
        float: The gradient as a percentage. Returns 0 if distance is 0.
    """
    if distance == 0:
        return 0

    # Convert distance to meters for gradient calculation
    return (elevation_diff / (distance * 1000)) * 100


def calculate_point_geo_data(point, previous_point):
    """
    Calculate geographical data for a point based on a previous point.

    Parameters:
        point: An object representing the current point with latitude, longitude, and elevation attributes.
        previous_point: An object representing the previous point with latitude, longitude, and elevation attributes.

    Returns:
        list: A list containing:
            - point_distance (float): Distance between the points in kilometers.
            - elevation_diff (float): Elevation difference between the points in meters.
            - gradient (float): Gradient between the points as a percentage.
    """
    point_distance = haversine(
        previous_point.latitude, previous_point.longitude, point.latitude, point.longitude
    )

    elevation_diff = point.elevation - previous_point.elevation
    gradient = calculate_gradient(point_distance, elevation_diff)

    return [point_distance, elevation_diff, gradient]
