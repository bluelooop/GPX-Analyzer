from collections import namedtuple

import csv
import os

import argparse
from dotenv import load_dotenv

from gpx import process_gpx


def write_on_csv(gpx_file, output_file, segment_length, ai_prompt=None):
    segments = process_gpx(gpx_file, segment_length, ai_prompt)

    # Prepare CSV output
    with open(output_file, 'w', newline='') as csvfile:
        # Create CSV writers - one for points and one for segments
        segment_writer = csv.writer(csvfile)
        columns = [
            'Segment', 'Start Elevation', 'End Elevation', 'Min Elevation', 'Max Elevation',
            'Distance(Km)', 'Start Km', 'End Km', 'Elevation Gain', 'Elevation Loss',
            'Avg Grade', 'Max grade', 'Min grade', 'Start time', 'End time', 'Duration'
        ]

        if ai_prompt:
            columns.append('Description')

        rows = []
        for segment in segments:
            row = [
                segment.number,
                segment.start_elevation,
                segment.end_elevation,
                segment.min_elevation,
                segment.max_elevation,
                segment.distance,
                segment.start_distance,
                segment.end_distance,
                segment.elevation_gain,
                segment.elevation_loss,
                segment.avg_grade,
                segment.max_grade,
                segment.min_grade,
            ]

            if segment.start_time:
                row.append(segment.start_time)
            else:
                if "Start time" in columns:
                    columns.remove("Start time")

            if segment.end_time:
                row.append(segment.end_time)
            else:
                if "End time" in columns:
                    columns.remove("End time")

            if segment.duration:
                row.append(segment.duration)
            else:
                if "Duration" in columns:
                    columns.remove("Duration")

            if ai_prompt:
                row.append(segment.description)

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
