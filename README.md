# NMBS Train Data Analysis

This project analyzes both planning data and real-time data from NMBS (Belgian Railways).

## Overview

The application processes four types of planning data:
- GTFS (General Transit Feed Specification) data in ZIP format
- NeTEx (Network Timetable Exchange) XML data
- Edifact format data
- Raw data files (such as rawdata_TC.zip)

It also analyzes real-time data which includes:
- Real-time data with platform change information
- Real-time data without platform change information

## Features

- Data analysis and statistics for different data formats
- Real-time data monitoring
- Interactive visualizations of train data
- **Route map visualization** showing all train routes on an interactive map

## Directory Structure

## How to run
- python main.py               # Run both analysis and web app
- python main.py --analyze-only # Run only the analysis
- python main.py --app-only     # Run only the web app

## Map Visualization
The application can visualize train routes on an interactive map. To view the map:
1. Launch the web app
2. Go to the "Maps" tab
3. Click "Generate Route Map"

The map will show all available train routes with stations as markers.
