import argparse
import csv
import os
import sys
from collections import namedtuple

from dotenv import load_dotenv

from gpx import get_routes, GPXError
from provider import is_valid_url, get_gpx_data


def write_on_csv(gpx_data_uri, output_file, segment_length):
    gpx_data = get_gpx_data(gpx_data_uri)

    try:
        routes = get_routes(gpx_data, segment_length)
    except GPXError as e:
        print(e, file=sys.stderr)
        return False

    if not routes:
        print(f"No routes found for {gpx_data_uri}", file=sys.stderr)
        return False

    # Prepare CSV output
    with open(output_file, 'w', newline='') as csvfile:
        # Create CSV writers - one for points and one for segments
        segment_writer = csv.writer(csvfile)
        columns = [
            'Segment', 'Start Elevation', 'End Elevation', 'Min Elevation', 'Max Elevation',
            'Distance(Km)', 'Start Km', 'End Km', 'Elevation Gain', 'Elevation Loss',
            'Avg Grade', 'Min grade', 'Max grade'
        ]

        rows = []
        for route in routes:
            for segment in route.segments:
                row = [
                    segment.number,
                    round(segment.start_elevation, 2),
                    round(segment.end_elevation, 2),
                    round(segment.min_elevation, 2),
                    round(segment.max_elevation, 2),
                    round(segment.distance, 2),
                    round(segment.start_distance, 2),
                    round(segment.end_distance, 2),
                    round(segment.elevation_gain, 2),
                    round(segment.elevation_loss, 2),
                    round(segment.avg_grade, 2),
                    round(segment.min_grade, 2),
                    round(segment.max_grade, 2),
                ]

                rows.append(row)

        segment_writer.writerow(columns)
        segment_writer.writerows(rows)

    print(f"Successfully processed {gpx_data_uri} to {output_file}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Convert GPX data to CSV with 1km segment analysis and AI descriptions')
    parser.add_argument('gpx_file_or_url', help='Path to GPX data')
    parser.add_argument('-o', '--output', help='Output CSV file (default: input_file_name.csv)')
    parser.add_argument('-l', '--segment-length', type=float, default=1.0,
                        help='Length of segments in kilometers (default: 1.0)')

    args = parser.parse_args()

    # Set default output file if not specified
    if not args.output:
        if is_valid_url(args.gpx_file_or_url):
            base_name = args.gpx_file_or_url.split("/")[-1]
        else:
            base_name = os.path.splitext(os.path.basename(args.gpx_file_or_url))[0]

        args.output = f"{base_name}.csv"

    result = write_on_csv(args.gpx_file_or_url, args.output, args.segment_length)

    if not result:
        print("Failed to process GPX data", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    EnvironmentFile = namedtuple("EnvironmentFile", ["file", "override"])

    env_file = EnvironmentFile(".env", False)
    env_local_file = EnvironmentFile(".env.local", True)

    for ef in [env_file, env_local_file]:
        load_dotenv(ef.file, override=ef.override)

    main()
