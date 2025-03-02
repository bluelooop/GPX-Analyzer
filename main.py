from collections import namedtuple

import csv
import os

import argparse
from dotenv import load_dotenv

from gpx import get_routes


def write_on_csv(gpx_file, output_file, segment_length, ai_prompt=None):
    routes = get_routes(gpx_file, segment_length, ai_prompt)

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

    print(f"Successfully processed {gpx_file} to {output_file}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Convert GPX file to CSV with 1km segment analysis and AI descriptions')
    parser.add_argument('gpx_file', help='Path to GPX file')
    parser.add_argument('-o', '--output', help='Output CSV file (default: input_file_name.csv)')
    parser.add_argument('-aip', '--ai-prompt', type=str,
                        help='Specify an AI prompt to use for descriptions')
    parser.add_argument('-l', '--segment-length', type=float, default=1.0,
                        help='Length of segments in kilometers (default: 1.0)')

    args = parser.parse_args()

    # Set default output file if not specified
    if not args.output:
        base_name = os.path.splitext(os.path.basename(args.gpx_file))[0]
        args.output = f"{base_name}.csv"

    write_on_csv(args.gpx_file, args.output, args.segment_length, args.ai_prompt)


if __name__ == "__main__":
    EnvironmentFile = namedtuple("EnvironmentFile", ["file", "override"])

    env_file = EnvironmentFile(".env", False)
    env_local_file = EnvironmentFile(".env.local", True)

    for ef in [env_file, env_local_file]:
        load_dotenv(ef.file, override=ef.override)

    main()
