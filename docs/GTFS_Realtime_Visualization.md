# GTFS Real-time Data Visualization Guide

This guide explains how to visualize GTFS (General Transit Feed Specification) real-time data, building on top of the information provided by Sean Barbeau and other transit data experts.

## Understanding GTFS Real-time Data

GTFS Real-time is a feed specification that allows public transportation agencies to provide real-time updates about their fleet to application developers. The feed is provided in Protocol Buffer format and includes:

- **Trip updates** - delays, cancellations, changed routes
- **Service alerts** - station/stop closures, important notifications
- **Vehicle positions** - where vehicles are located in real-time

## Visualizing GTFS Real-time Data

### Option 1: Using Existing Tools

Several ready-made tools can help you visualize GTFS real-time data:

1. **OpenTripPlanner** - An open-source platform for multi-modal trip planning
   - http://www.opentripplanner.org/

2. **OneBusAway** - A suite of transit tools focused on real-time arrival information
   - https://github.com/OneBusAway/onebusaway-application-modules

3. **OneBusAway GTFS-realtime Visualizer** - A lightweight tool specifically for visualizing vehicle positions
   - https://github.com/OneBusAway/onebusaway-gtfs-realtime-visualizer

4. **TransitVis** - Visualizes GTFS schedules and real-time data
   - https://github.com/mobilitydata/transitvis

### Option 2: Building Your Own Visualizer

If you're building your own visualizer:

1. Set up a basic web server (Node.js, Python Flask, or similar)
2. Use the GTFS-realtime bindings to parse the data
   - https://github.com/MobilityData/gtfs-realtime-bindings
3. Store the parsed data in a format suitable for visualization
4. Use a mapping library like Leaflet or Mapbox to display the data
5. Set up a polling mechanism to fetch updates every 30 seconds

#### Sample Code Structure:

```python
# Using Python with Flask and GTFS-realtime-bindings
from flask import Flask, render_template
from google.transit import gtfs_realtime_pb2
import requests
import json

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('map.html')

@app.route('/api/vehicle-positions')
def get_vehicle_positions():
    # Fetch GTFS-realtime feed
    feed = gtfs_realtime_pb2.FeedMessage()
    response = requests.get('URL_TO_VEHICLE_POSITIONS_FEED')
    feed.ParseFromString(response.content)
    
    # Process and format data for front-end
    vehicles = []
    for entity in feed.entity:
        if entity.HasField('vehicle'):
            vehicle = {
                'id': entity.vehicle.vehicle.id,
                'lat': entity.vehicle.position.latitude,
                'lon': entity.vehicle.position.longitude,
                'bearing': entity.vehicle.position.bearing,
                'speed': entity.vehicle.position.speed,
                'trip_id': entity.vehicle.trip.trip_id if entity.vehicle.HasField('trip') else None
            }
            vehicles.append(vehicle)
    
    return json.dumps(vehicles)

if __name__ == '__main__':
    app.run(debug=True)
```

## Implementation for NMBS/SNCB Data

For Belgian Railways (NMBS/SNCB) data:

1. The GTFS static data is updated daily
2. Real-time data is updated every 30 seconds
3. Real-time information is available for 6 hours

When implementing a visualizer:

1. Use the static GTFS data to build your base transit network
2. Overlay real-time updates to show actual train positions, delays, and platform changes
3. Poll for new data every 30 seconds to keep information current
4. Consider implementing a caching mechanism to reduce load on the NMBS/SNCB API

## Useful Resources

- [GTFS Realtime Reference](https://gtfs.org/realtime/)
- [GTFS Best Practices](https://gtfs.org/best-practices/)
- [Awesome Transit](https://github.com/CUTR-at-USF/awesome-transit) - A collection of transit tools and resources
- [What's new in GTFS Realtime v2.0](https://barbeau.medium.com/whats-new-in-gtfs-realtime-v2-0-cd45e6a861e9)

## Visualization Tips

- Use different colors to distinguish between on-time and delayed vehicles
- Provide visual indicators for platform changes
- Allow users to filter by route or service type
- Include a time slider to see how transit patterns change throughout the day
- Consider adding alerts or notifications for significant delays
