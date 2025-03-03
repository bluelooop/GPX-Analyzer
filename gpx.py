import gpxpy
import gpxpy.gpx
from gpxpy.gpx import GPXTrackSegment, GPXTrackPoint

from provider import get_locations_elevations
from utils import haversine, calculate_gradient


class GPXError(Exception):
    pass


class RoutePoint(GPXTrackPoint):
    """
    Represents a point on a route, extending a GPX track point by adding
    distance, cumulative distance, and grade calculations.
    """

    def __init__(self, gpx_point: GPXTrackPoint):
        super().__init__(
            gpx_point.latitude, gpx_point.longitude, gpx_point.elevation,
            gpx_point.time, gpx_point.symbol, gpx_point.comment,
            gpx_point.horizontal_dilution, gpx_point.vertical_dilution, gpx_point.position_dilution,
            gpx_point.speed, gpx_point.name
        )

        self.distance = 0
        self.cumulative_distance = 0
        self.grade = 0

    def calculate_distance_and_grade(self, previous_point: 'RoutePoint'):
        """
        Calculate the distance and grade between this point and a previous point.
    
        Parameters:
            previous_point (RoutePoint): The previous point in the route for reference.
        """
        elevation_diff = self.get_elevation_difference(previous_point)

        self.distance = haversine(
            previous_point.latitude, previous_point.longitude, self.latitude, self.longitude
        )
        self.grade = calculate_gradient(self.distance, elevation_diff)

        self.cumulative_distance += self.distance

    def get_elevation_difference(self, previous_point: 'RoutePoint'):
        """
        Compute the elevation difference between this point and a previous point.
    
        Parameters:
            previous_point (RoutePoint): The previous point in the route for reference.
    
        Returns:
            float: The difference in elevation between this point and the previous point.
        """
        return self.elevation - previous_point.elevation


class RouteSegment:
    """
    Represents a segment of a route, handling points, distances, grades,
    and elevation statistics calculations.
    """

    def __init__(self, gpx_segment: GPXTrackSegment):
        self._gpx_segment = gpx_segment

        self.number: int | None = None

        self.distance = 0

        self.avg_grade = 0
        self.max_grade = 0
        self.min_grade = 0

        self.min_elevation = 0
        self.max_elevation = 0

        self.start_elevation = 0
        self.end_elevation = 0

        self.elevation_gain = 0
        self.elevation_loss = 0

        self.start_distance = 0
        self.end_distance = 0

        self.duration: str = ""

        self.__start_point = None
        self.__end_point = None
        self.__points: list[RoutePoint] = []

        self.__grades: list[float] = []

    def __calculate_duration(self) -> str | None:
        if self.__start_point.time and self.__end_point.time:
            difference_seconds = self.__start_point.time_difference(self.__end_point)
            hours, remainder = divmod(difference_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            self.duration = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"

    def __calculate_statistics(self):
        elevations = [p.elevation for p in self.__points]

        self.min_elevation = min(elevations)
        self.max_elevation = max(elevations)

        self.avg_grade = sum(self.__grades) / len(self.__grades) if self.__grades else 0
        self.min_grade = min(self.__grades) if self.__grades else 0
        self.max_grade = max(self.__grades) if self.__grades else 0

    def calculate_elevation_gain_and_loss(self, point: RoutePoint, previous_point: RoutePoint):
        """
        Calculate the elevation gain and loss between two points.
    
        Parameters:
            point (RoutePoint): The current point in the segment.
            previous_point (RoutePoint): The previous point in the segment.
        """
        elevation_diff = point.get_elevation_difference(previous_point)

        if elevation_diff > 0:
            self.elevation_gain += elevation_diff
        elif elevation_diff < 0:
            self.elevation_loss += abs(elevation_diff)

    def add_point(self, point: RoutePoint):
        """
        Add a point to the segment, updating the list of points, grades,
        and cumulative distance.
    
        Parameters:
            point (RoutePoint): The point to be added to the segment.
        """
        self.__points.append(point)
        self.__grades.append(point.grade)

        self.distance = sum([p.distance for p in self.__points])

    def is_completed(self, current_point_index, max_length: float):
        """
        Determine if the segment has reached its maximum length or last point.
    
        Parameters:
            current_point_index (int): The index of the current point being processed.
            max_length (float): The maximum length allowed for the segment (in kilometers).
    
        Returns:
            bool: True if the segment is completed, False otherwise.
        """
        return (
                self.distance >= max_length
                or current_point_index == len(self._gpx_segment.points) - 1
                and len(self.__points) >= 2
        )

    def calculate_points_data(self):
        """
        Perform final calculations for the segment, setting start/end points,
        duration, elevation statistics, and grades.
        """
        self.__start_point = self.__points[0]
        self.__end_point = self.__points[-1]

        self.start_elevation = self.__start_point.elevation
        self.end_elevation = self.__end_point.elevation

        self.__calculate_duration()
        self.__calculate_statistics()


class Route:
    """
    Represents an entire route consisting of multiple segments, managing overall
    distance, elevation gain, and other aggregate statistics.
    """

    def __init__(self):
        self.name = ""
        self.description = ""

        self.distance = 0
        self.elevation_gain = 0
        self.elevation_loss = 0

        self.segments: list[RouteSegment] = []

    def add_segment(self, segment: RouteSegment):
        """
        Add a segment to the route and update overall distance and elevation data.
    
        Parameters:
            segment (RouteSegment): The segment to add to the route.
        """
        if segment.number is None:
            segment.number = len(self.segments) + 1

        self.segments.append(segment)

        segment.start_distance = self.distance

        self.distance += segment.distance

        segment.end_distance = self.distance

        self.elevation_gain += segment.elevation_gain
        self.elevation_loss += segment.elevation_loss


def get_points_elevations(points: list[GPXTrackPoint]) -> list[GPXTrackPoint]:
    """
    Retrieve elevation data for a list of GPXTrackPoints.

    Parameters:
        points (list[GPXTrackPoint]): A list of GPXTrackPoint objects without elevation data.

    Returns:
        list[GPXTrackPoint]: A list of GPXTrackPoint objects with updated elevation data.

    The function performs the following steps:
        1. Extracts latitude and longitude from each GPXTrackPoint to create a list of locations.
        2. Calls the `get_locations_elevations` function to fetch elevation data for each location.
        3. Constructs new GPXTrackPoint objects, adding the elevation values returned from the
           elevation service.
    """
    locations = [{"position": p_idx, "latitude": p.latitude, "longitude": p.longitude} for p_idx, p in
                 enumerate(points)]
    locations = get_locations_elevations(locations)

    return [
        GPXTrackPoint(
            latitude=location["latitude"],
            longitude=location["longitude"],
            elevation=location["elevation"]
        ) for location in locations
    ]


def get_routes(gpx_data: str, segment_length: float = 1.0) -> list[Route] | None:
    """
    Parse GPX data and generate a list of Route objects, which are segmented based on a given maximum segment length.

    Parameters:
        gpx_data (str): The GPX data to be processed, provided as a string.
        segment_length (float): The maximum length (in kilometers) for each segment in the route.

    Returns:
        list[Route] | None: A list of Route objects representing the parsed GPX data. Returns None if an error occurs.

    Raises:
        GPXError: If there is an issue with parsing the GPX data or processing the routes.

    The function processes the GPX data as follows:
        1. Parses the GPX data string using the gpxpy library.
        2. Creates `Route` objects for each track found in the GPX data.
        3. Splits tracks into segments (`RouteSegment`) based on the specified maximum length.
        4. Calculates statistics such as distance, elevation gain/loss, and duration for each segment.
        5. Adds segments to their respective routes and returns the complete list of routes.
    """
    try:
        gpx = gpxpy.parse(gpx_data)

        routes = []
        # Process tracks
        for track_idx, track in enumerate(gpx.tracks):
            route = Route()
            route.name = track.name
            route.description = track.description

            for segment_idx, segment in enumerate(track.segments):
                route_segment = RouteSegment(segment)

                # Variables for point-to-point calculations
                previous_point: RoutePoint | None = None

                # Process points
                points = segment.points
                if any([p.elevation == 0.0 for p in points]):
                    points = get_points_elevations(points)

                for point_idx, point in enumerate(points):
                    route_point = RoutePoint(point)

                    # Skip points without elevation data
                    if not route_point.has_elevation() or previous_point is None:
                        previous_point = route_point
                        continue

                    route_point.calculate_distance_and_grade(previous_point)

                    route_segment.calculate_elevation_gain_and_loss(route_point, previous_point)
                    route_segment.add_point(route_point)

                    # Check if we've completed a segment
                    if route_segment.is_completed(point_idx, segment_length):
                        route_segment.calculate_points_data()

                        route.add_segment(route_segment)
                        route_segment = RouteSegment(segment)

                    # Update previous point
                    previous_point = route_point

            routes.append(route)
        return routes

    except Exception as e:
        raise GPXError(f"Error processing GPX file: {e}") from e
