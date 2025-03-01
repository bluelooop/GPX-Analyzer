import datetime
from typing import NamedTuple

import gpxpy
import gpxpy.gpx
from gpxpy.gpx import GPXTrackSegment

from ai import generate_segment_description
from utils import calculate_point_geo_data


class GPXPoint(NamedTuple):
    """
    Represents a single point in a GPX segment with geographical and related data.

    Attributes:
        latitude (float): Latitude of the point in degrees.
        longitude (float): Longitude of the point in degrees.
        elevation (float): Elevation of the point in meters.
        time (datetime.time | None): Time associated with the point, if available.
        speed (float | None): Speed at the point, if available.
    """
    latitude: float
    longitude: float
    elevation: float
    time: datetime.time | None
    speed: float | None


class GPXSegment(NamedTuple):
    """
    Represents a segment of a GPX track with detailed statistics.

    Attributes:
        number (int): Segment number within the GPX track.
        start_elevation (float): Elevation at the start of the segment in meters.
        end_elevation (float): Elevation at the end of the segment in meters.
        min_elevation (float): The minimum elevation in the segment in meters.
        max_elevation (float): The maximum elevation in the segment in meters.
        distance (float): Length of the segment in kilometers.
        start_distance (float): Distance from the start of the track at the segment's start in kilometers.
        end_distance (float): Distance from the start of the track at the segment's end in kilometers.
        elevation_gain (float): Total positive elevation change in the segment in meters.
        elevation_loss (float): Total negative elevation change in the segment in meters.
        avg_grade (float): Average grade (in percentage) for the segment.
        max_grade (float): Maximum grade (in percentage) in the segment.
        min_grade (float): Minimum grade (in percentage) in the segment.
        start_time (str | None): Start time of the segment, if available.
        end_time (str | None): End time of the segment, if available.
        duration (str | None): Duration of the segment as a formatted string (HH:MM:SS), if available.
        description (str): A textual description of the segment.
    """
    number: int
    start_elevation: float
    end_elevation: float
    min_elevation: float
    max_elevation: float
    distance: float
    start_distance: float
    end_distance: float
    elevation_gain: float
    elevation_loss: float
    avg_grade: float
    max_grade: float
    min_grade: float
    start_time: str | None
    end_time: str | None
    duration: str | None
    description: str | None


def __get_segment_points(segment: GPXTrackSegment) -> list[GPXPoint] | list:
    """
    Extracts a list of points from a GPXTrackSegment and formats them as GPXPoint instances.

    Args:
        segment (GPXTrackSegment): The GPX segment to extract points from.

    Returns:
        list[GPXPoint] | list: A list of GPXPoint objects or an empty list if there are no points in the segment.
    """

    if not segment.points:
        return []

    points = [
        GPXPoint(
            latitude=round(p.latitude, 6),
            longitude=round(p.longitude, 6),
            elevation=p.elevation,
            time=p.time,
            speed=p.speed
        )
        for p in segment.points
    ]

    return points


def __update_elevation_data(elevation_gain: float, elevation_loss: float, distance_diff: float):
    """
    Updates the cumulative elevation gain and loss based on distance differences.

    Args:
        elevation_gain (float): Cumulative elevation gain before this update.
        elevation_loss (float): Cumulative elevation loss before this update.
        distance_diff (float): Difference in elevation between two points.

    Returns:
        list[float, float]: Updated elevation gain and loss values.
    """
    if distance_diff > 0:
        elevation_gain += distance_diff
    elif distance_diff < 0:
        elevation_loss += abs(distance_diff)

    return [elevation_gain, elevation_loss]


def __calculate_segment_statistics(
        segment_points: list, segment_grades: list
) -> tuple[float, float, float, float, float]:
    """
    Calculates key statistics (elevations and grades) for a GPX segment.

    Args:
        segment_points (list): List of dictionaries containing point data for a segment.
        segment_grades (list): List of grade percentages for the segment.

    Returns:
        tuple[float, float, float, float, float]: Minimum elevation, maximum elevation, 
        average grade, maximum grade, and minimum grade for the segment.
    """
    elevations = [p['point'].elevation for p in segment_points]

    min_elevation = min(elevations)
    max_elevation = max(elevations)

    # Calculate average grade
    avg_grade = sum(segment_grades) / len(segment_grades) if segment_grades else 0
    max_grade = max(segment_grades) if segment_grades else 0
    min_grade = min(segment_grades) if segment_grades else 0

    return min_elevation, max_elevation, avg_grade, max_grade, min_grade


def __calculate_segment_duration(start_point: GPXPoint, end_point: GPXPoint) -> str | None:
    """
    Calculates the time duration between two points in a GPX segment.

    Args:
        start_point (GPXPoint): Starting point of the segment with time data.
        end_point (GPXPoint): Ending point of the segment with time data.

    Returns:
        str | None: Duration formatted as HH:MM:SS if time data exists, otherwise None.
    """
    if start_point.time and end_point.time:
        duration_seconds = (end_point.time - start_point.time).total_seconds()
        hours, remainder = divmod(duration_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"


def __process_segment(segment: dict, ai_prompt: str | None = None):
    """
    Processes a single GPX track segment and returns a GPXSegment object with detailed metadata.

    Args:
        segment (dict): A dictionary containing raw segment data, including points, 
            elevations, distances, gradients, and other metrics.
        ai_prompt (str | None, optional): A string prompt for generating segment 
            descriptions using an AI service. Defaults to None.

    Returns:
        GPXSegment: An object encapsulating all processed and formatted 
            segment statistics, including elevation data, distance data, grades, 
            time duration, and optionally an AI-generated description.
    """

    # Calculate duration if time data is available
    duration = __calculate_segment_duration(segment["start_point"], segment["end_point"])

    description = generate_segment_description(segment, ai_prompt) if ai_prompt else None

    return GPXSegment(
        segment['number'],
        round(segment["start_point"].elevation, 2),
        round(segment["end_point"].elevation, 2),
        round(segment["min_elevation"], 2),
        round(segment["max_elevation"], 2),
        round(segment["distance"], 2),
        round(segment["start_distance"], 2),
        round(segment["start_distance"] + segment["distance"], 2),
        round(segment["elevation_gain"], 2),
        round(segment["elevation_loss"], 2),
        round(segment["avg_grade"], 2),
        round(segment["max_grade"], 2),
        round(segment["min_grade"], 2),
        segment["start_point"].time.isoformat() if segment["start_point"].time else '',
        segment["end_point"].time.isoformat() if segment["end_point"].time else '',
        duration,
        description
    )


def process_gpx(gpx_file: str, segment_length: float = 1.0, ai_prompt=None) -> list[GPXSegment]:
    """
    Processes a GPX file to divide its tracks into segments based on the specified
    segment length, while extracting detailed information about the tracks, points,
    elevations, gradients, and related data. Each segment includes cumulative metrics
    and may optionally integrate AI-generated data based on a provided prompt.

    :param gpx_file: The path to the GPX file that contains the geographical and
        track data to be processed.
    :type gpx_file: str
    :param segment_length: Specifies the length of each generated segment in kilometers.
        The function will split the tracks into segments approximately matching this
        distance. Default value is 1.0.
    :type segment_length: float
    :param ai_prompt: An optional parameter to provide a custom AI prompt to process
        each completed segment. AI output can enhance or customize the segment metadata.
    :type ai_prompt: Any
    :return: A list of dictionaries where each dictionary represents a processed
        segment. Each segment includes details such as distance, elevation gain/loss,
        gradient, segment number, and optionally AI-enhanced data.
    :rtype: list
    """
    try:
        # Parse GPX file
        with open(gpx_file, 'r') as f:
            gpx = gpxpy.parse(f)

            segments = []
            # Process tracks
            for track_idx, track in enumerate(gpx.tracks):
                for segment_idx, segment in enumerate(track.segments):
                    # Variables for tracking segment data
                    cumulative_distance = 0
                    segment_start_distance = 0
                    segment_distance = 0
                    segment_points = []
                    segment_grades = []
                    segment_elevation_gain = 0
                    segment_elevation_loss = 0
                    segment_number = 1

                    # Variables for point-to-point calculations
                    previous_point: GPXPoint | None = None
                    previous_duration = None

                    # Process points
                    for point_idx, point in enumerate(__get_segment_points(segment)):
                        # Skip points without elevation data
                        if point.elevation == 0 and previous_duration is None:
                            continue

                        # Calculate distance from previous point
                        point_distance = 0
                        gradient = 0

                        if previous_point:
                            point_distance, elevation_diff, gradient = calculate_point_geo_data(point, previous_point)

                            cumulative_distance += point_distance
                            segment_distance += point_distance
                            segment_grades.append(gradient)

                            segment_elevation_gain, segment_elevation_loss = __update_elevation_data(
                                segment_elevation_gain, segment_elevation_loss, elevation_diff
                            )

                        # Add point to current segment
                        segment_points.append({
                            'point': point,
                            'distance': point_distance,
                            'cumulative_distance': cumulative_distance,
                            'gradient': gradient
                        })

                        # Check if we've completed a segment
                        if (
                                segment_distance >= segment_length
                                or point_idx == len(segment.points) - 1
                                and len(segment_points) >= 2
                        ):
                            start_point: GPXPoint = segment_points[0]['point']
                            end_point: GPXPoint = segment_points[-1]['point']

                            # Calculate segment statistics
                            min_elevation, max_elevation, avg_grade, max_grade, min_grade = (
                                __calculate_segment_statistics(segment_points, segment_grades)
                            )

                            segments.append(
                                {
                                    "number": segment_number,
                                    'distance': segment_distance,
                                    'elevation_gain': segment_elevation_gain,
                                    'elevation_loss': segment_elevation_loss,
                                    'avg_grade': avg_grade,
                                    'max_grade': max_grade,
                                    'min_grade': min_grade,
                                    "min_elevation": min_elevation,
                                    "max_elevation": max_elevation,
                                    "start_distance": segment_start_distance,
                                    "start_point": start_point,
                                    "end_point": end_point,
                                }
                            )

                            # Reset segment data
                            segment_number += 1
                            segment_start_distance = cumulative_distance
                            segment_distance = 0
                            segment_points = []
                            segment_grades = []
                            segment_elevation_gain = 0
                            segment_elevation_loss = 0

                            # Update previous point
                        previous_point = point
                        previous_duration = point.elevation

        return [__process_segment(segment, ai_prompt) for segment in segments]

    except Exception as e:
        print(f"Error processing GPX file: {e}")
        return []
