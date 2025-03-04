# GPX Analyzer

**GPX Analyzer** is a Python library designed to process and analyze GPX (GPS Exchange Format) files, which are commonly
used to store GPS data from devices like fitness trackers, smartphones, and GPS devices. The library enables users to
load GPX data and extract useful information such as elevation, grades, elevation gain/loss, and other metadata. It is
particularly
useful for developers who need to work with GPS data for activities like hiking, cycling, or running.

## Features

- Parse and analyze GPX data with ease.
- Extract data such as waypoints, tracks, and routes.
- Provide statistics like distance, elevation, elevation gain/loss, grade.
- Visualize or further process the data for various applications.

---

## Clone

You can use GPX Analyzer by clone it:

```bash
git clone https://github.com/bluelooop/GPX-Analyzer.git
cd GPX-Analyzer
cp .env.sample .env.local
cp test/.env.sample test/.env.test.local
# Change both env local files with the required environment variables
```

Happy coding 😊

---

## Example Usage

Below is an example of how to use the **GPX Analyzer**:

```bash
export STRAVA_ACCESS_KEY="STRAVA_ACCESS_KEY"  # To get route data using the strava route link
export GOOGLE_ELEVATION_API_KEY="GOOGLE_ELEVATION_API_KEY" # If you want to use Google Elevation API to get elevations
python gpx_analyzer.py example.gpx -l10
python gpx_analyzer.py https://www.strava.com/routes/3331429303542262604 -l10
```

---

## Contributing

If you'd like to contribute to the development of GPX Analyzer, feel free to open issues or submit pull requests to the
repository. Contributions are always welcome!

---

## License

GPX Analyzer is released under the [GPL v3.0 License](https://opensource.org/license/gpl-3-0).