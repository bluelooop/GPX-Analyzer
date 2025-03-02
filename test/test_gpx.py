from gpxpy.gpx import GPXTrackPoint, GPXTrackSegment

from gpx import RoutePoint, RouteSegment


class TestRoutePoint:

    def test_calculate_distance_and_grade(self):
        # Create two RoutePoint objects with example coordinates and elevations
        point1 = RoutePoint(GPXTrackPoint(latitude=52.5200, longitude=13.4050, elevation=34.0))
        point2 = RoutePoint(GPXTrackPoint(latitude=52.5201, longitude=13.4051, elevation=54.0))

        # Calculate distance and grade between the two points
        point1.calculate_distance_and_grade(point2)

        # Validate the calculated distance (rounded for comparison)
        assert round(point1.distance, 5) == 0.01302

        # Validate the calculated grade
        assert abs(round(point1.grade, 2)) == 153.65

    def test_get_elevation_difference(self):
        # Create two RoutePoint objects with example elevations
        # Aware that point1 and point2 does not describe point1 -> point2 direction
        point1 = RoutePoint(GPXTrackPoint(elevation=34.0))
        point2 = RoutePoint(GPXTrackPoint(elevation=54.0))

        # Calculate elevation difference
        elevation_difference = point1.get_elevation_difference(point2)

        # Validate the calculated elevation difference
        assert abs(elevation_difference) == 20.0


class TestRouteSegment:

    def test_calculate_elevation_gain_and_loss(self):
        # Create a RouteSegment with two RoutePoint objects
        # Aware that point1 and point2 does not describe point1 -> point2 direction
        point1 = RoutePoint(GPXTrackPoint(elevation=34.0))
        point2 = RoutePoint(GPXTrackPoint(elevation=54.0))
        segment = RouteSegment(GPXTrackSegment([
            GPXTrackPoint(elevation=34.0),
            GPXTrackPoint(elevation=54.0)
        ]))

        # Calculate elevation gain and loss for the segment
        segment.calculate_elevation_gain_and_loss(point1, point2)

        # Validate the calculated elevation gain
        assert abs(segment.elevation_gain) == 0

        # Validate the calculated elevation loss is 0, as it is uphill
        assert abs(segment.elevation_loss) == 20.0
