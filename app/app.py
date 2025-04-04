import dash
from dash import dcc, html, Input, Output, callback_context
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json
import os
import ast
from train_data_overview import TrainDataAnalyzer

# Set dark mode theme colors
dark_bg_color = "#121212"
dark_paper_color = "#1e1e1e"
dark_text_color = "#e0e0e0"
dark_grid_color = "#333333"

# Initialize the Dash app with dark theme
app = dash.Dash(
    __name__, 
    title="NMBS Train Data Analysis",
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)

# Dark theme for Plotly figures
dark_template = go.layout.Template(
    layout=dict(
        paper_bgcolor=dark_paper_color,
        plot_bgcolor=dark_bg_color,
        font=dict(color=dark_text_color),
        xaxis=dict(gridcolor=dark_grid_color, zerolinecolor=dark_grid_color),
        yaxis=dict(gridcolor=dark_grid_color, zerolinecolor=dark_grid_color),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=dark_text_color)),
        title=dict(font=dict(color=dark_text_color)),
        margin=dict(l=40, r=20, t=40, b=40),
    )
)

# Load overview data
try:
    with open('train_data_overview.json', 'r') as f:
        overview_data = json.load(f)
except FileNotFoundError:
    # Generate new overview if file doesn't exist
    analyzer = TrainDataAnalyzer()
    overview_data = analyzer.generate_overview()
    analyzer.save_overview(overview_data)

# Helper function to parse string representations of dictionaries
def parse_string_dict(string_dict):
    """Parse a string representation of a dictionary into an actual dictionary"""
    if isinstance(string_dict, str):
        try:
            return ast.literal_eval(string_dict)
        except:
            return {}
    return string_dict

# Prepare GTFS data for visualization
def get_gtfs_data():
    gtfs_stats = overview_data.get('gtfs_stats', {})
    if not gtfs_stats:
        return None
    
    # Find the GTFS file with actual data
    for file_name, file_stats in gtfs_stats.items():
        # Parse string representation if needed
        file_stats = parse_string_dict(file_stats)
        
        if file_stats.get('total_records', 0) > 0:
            tables_data = file_stats.get('tables', {})
            # Return actual counts for visualization
            return {
                'category': [table.replace('.txt', '') for table in tables_data.keys()],
                'count': [info.get('record_count', 0) for info in tables_data.values()]
            }
    
    return None

# Get real-time data
def get_realtime_data():
    realtime_data = {
        'with_changes': int(overview_data.get('realtime_data', {}).get('with_platform_changes', 0)),
        'without_changes': int(overview_data.get('realtime_data', {}).get('without_platform_changes', 0))
    }
    return realtime_data

# App layout
app.layout = html.Div([
    html.H1("NMBS Train Data Analysis"),
    
    # Tabs for different sections
    dcc.Tabs([
        # Overview Tab
        dcc.Tab(label="Overview", children=[
            html.Div([
                html.H2("Data Overview"),
                html.Div([
                    html.Div([
                        html.H3("Planning Data"),
                        html.P(f"GTFS Files: {overview_data.get('planning_data', {}).get('gtfs_files', 0)}"),
                        html.P(f"NeTEx Files: {overview_data.get('planning_data', {}).get('netex_files', 0)}"),
                        html.P(f"Edifact Files: {overview_data.get('planning_data', {}).get('edifact_files', 0)}"),
                        html.P(f"Raw Data Files: {overview_data.get('planning_data', {}).get('rawdata_files', 0)}")
                    ], className="info-box"),
                    
                    html.Div([
                        html.H3("Real-time Data"),
                        html.P(f"With Platform Changes: {overview_data.get('realtime_data', {}).get('with_platform_changes', 0)}"),
                        html.P(f"Without Platform Changes: {overview_data.get('realtime_data', {}).get('without_platform_changes', 0)}")
                    ], className="info-box")
                ], style={"display": "flex", "justifyContent": "space-around"}),
                
                html.Div([
                    html.H3("Data Format Relationships"),
                    html.P("European public transit data is typically available in these formats:"),
                    html.Ul([
                        html.Li("GTFS - General Transit Feed Specification (developed by Google)"),
                        html.Li("NeTEx - Network Timetable Exchange (European standard)"),
                        html.Li("SIRI - Service Interface for Real Time Information (for real-time data)")
                    ]),
                    html.P("NMBS/SNCB provides both GTFS and NeTEx for schedule data, plus real-time updates.")
                ], className="info-box")
            ])
        ]),
        
        # Visualizations Tab
        dcc.Tab(label="Visualizations", children=[
            html.Div([
                html.H2("Data Visualizations"),
                
                html.Div([
                    html.Label("Select Data Type:"),
                    dcc.Dropdown(
                        id='data-type-dropdown',
                        options=[
                            {'label': 'Planning Data (GTFS)', 'value': 'gtfs'},
                            {'label': 'Planning Data (NeTEx)', 'value': 'netex'},
                            {'label': 'Real-time Data', 'value': 'realtime'},
                            {'label': 'Data Format Comparison', 'value': 'format_comparison'},
                            {'label': 'Raw Data Overview', 'value': 'rawdata'}
                        ],
                        value='gtfs'
                    )
                ], style={"width": "50%", "margin": "20px auto"}),
                
                dcc.Graph(id='main-graph')
            ])
        ]),
        
        # Details Tab
        dcc.Tab(label="Data Details", children=[
            html.Div([
                html.H2("Data Details"),
                html.Div([
                    html.Label("Select Data Type:"),
                    dcc.Dropdown(
                        id='details-type-dropdown',
                        options=[
                            {'label': 'Planning Data (GTFS)', 'value': 'gtfs'},
                            {'label': 'Planning Data (NeTEx)', 'value': 'netex'},
                            {'label': 'Real-time Data', 'value': 'realtime'},
                            {'label': 'Raw Data', 'value': 'rawdata'}
                        ],
                        value='gtfs'
                    )
                ], style={"width": "50%", "margin": "20px auto"}),
                html.Div(id='data-details')
            ])
        ]),
        
        # Real-time Monitor Tab
        dcc.Tab(label="Real-time Monitor", children=[
            html.Div([
                html.H2("Real-time Data Monitoring"),
                html.Div([
                    html.P("Monitor real-time data from NMBS by checking the following directories:"),
                    html.Ul([
                        html.Li("With platform changes: data/Real-time_gegevens/real-time_gegevens_met_info_over_spoorveranderingen"),
                        html.Li("Without platform changes: data/Real-time_gegevens/real-time_gegevens_zonder_info_over_spoorveranderingen")
                    ]),
                    
                    html.H3("How to Use Real-time Data"),
                    html.P("GTFS Realtime is an extension to GTFS that provides real-time updates about:"),
                    html.Ul([
                        html.Li("Trip updates (delays, cancellations, changed routes)"),
                        html.Li("Service alerts (station/stop closures, important notifications)"),
                        html.Li("Vehicle positions (where vehicles are located in real time)")
                    ]),
                    
                    html.H3("Sample Real-time Data"),
                    html.P("Sample files have been created to demonstrate the real-time data structure."),
                    html.P("These samples show the format of train delay and platform change information."),
                    
                    html.Button("Update Data", id="update-button", n_clicks=0),
                    html.Div(id='update-status')
                ], className="info-box")
            ])
        ]),
        
        # Maps Tab
        dcc.Tab(label="Maps", children=[
            html.Div([
                html.H2("Train Route Map"),
                html.P("Visualize train routes on an interactive map. This shows the network of routes based on available data."),
                html.Div([
                    html.Button("Generate Route Map", id="generate-map-button", className="button"),
                    html.Div(id="map-status"),
                ], style={"margin": "20px 0"}),
                html.Div([
                    html.Iframe(
                        id="map-iframe",
                        style={"width": "100%", "height": "600px", "border": "none"},
                        src=""
                    )
                ], id="map-container", style={"display": "none"})
            ])
        ])
    ])
])

@app.callback(
    Output('main-graph', 'figure'),
    Input('data-type-dropdown', 'value')
)
def update_graph(data_type):
    # Create a base figure with dark mode template
    fig = go.Figure(layout=dict(template=dark_template))
    
    if data_type == 'gtfs':
        # Use actual GTFS data for visualization
        gtfs_data = get_gtfs_data()
        if gtfs_data:
            fig = px.bar(gtfs_data, x='category', y='count', title='GTFS Data Overview',
                         template="plotly_dark")
            # Sort by count descending for better visualization
            fig.update_layout(xaxis={'categoryorder':'total descending'})
        else:
            fig.update_layout(title="No GTFS data available")
        
    elif data_type == 'netex':
        # NeTEx visualization
        netex_stats = overview_data.get('netex_stats', {})
        if netex_stats:
            # Get the first file's stats
            first_file_name = next(iter(netex_stats))
            first_file = netex_stats[first_file_name]
            
            # Parse if it's a string
            first_file = parse_string_dict(first_file)
            
            categories = list(first_file.keys())
            counts = list(first_file.values())
            fig = px.bar(x=categories, y=counts, title='NeTEx Element Counts',
                         template="plotly_dark")
        else:
            fig.update_layout(title="No NeTEx data available")
            
    elif data_type == 'realtime':
        # Real-time data visualization
        realtime_data = get_realtime_data()
        data = {'category': ['With platform changes', 'Without platform changes'],
                'count': [realtime_data['with_changes'], realtime_data['without_changes']]}
        
        fig = px.bar(data, x='category', y='count', title='Real-time Data Overview',
                     template="plotly_dark", color_discrete_sequence=['#4dabf7', '#74c0fc'])
        
        # Add note if no data
        if sum(data['count']) == 0:
            fig.add_annotation(
                text="No real-time data files found. Check directories exist and contain data.",
                showarrow=False,
                x=0.5,
                y=0.5,
                xref="paper",
                yref="paper"
            )
    
    elif data_type == 'rawdata':
        # Raw data visualization
        rawdata_stats = overview_data.get('rawdata_stats', {})
        if rawdata_stats:
            # Create sunburst chart of file types
            try:
                # Extract file types from first raw data file
                first_file_name = next(iter(rawdata_stats))
                file_types = parse_string_dict(rawdata_stats[first_file_name].get('file_types', '{}'))
                
                if file_types:
                    labels = []
                    parents = []
                    values = []
                    
                    # Add root
                    labels.append('Raw Data')
                    parents.append('')
                    values.append(sum(parse_string_dict(file_types).values()))
                    
                    # Add file types
                    for ext, count in parse_string_dict(file_types).items():
                        labels.append(ext if ext else 'no_extension')
                        parents.append('Raw Data')
                        values.append(count)
                    
                    fig = go.Figure(go.Sunburst(
                        labels=labels,
                        parents=parents,
                        values=values,
                    ))
                    fig.update_layout(title='Raw Data File Types', template="plotly_dark")
                else:
                    # Fallback to bar chart
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        x=[first_file_name],
                        y=[parse_string_dict(rawdata_stats[first_file_name]).get('file_count', 0)],
                        name='File Count'
                    ))
                    fig.update_layout(title='Raw Data File Count', template="plotly_dark")
            except Exception as e:
                fig.update_layout(title=f"Error creating raw data visualization: {str(e)}")
        else:
            fig.update_layout(title="No raw data available")
    
    elif data_type == 'format_comparison':
        # Create a comparison visualization of data formats
        fig = go.Figure()
        
        # Format comparison data
        formats = ['GTFS', 'NeTEx', 'GTFS Realtime', 'SIRI']
        static_support = [5, 5, 0, 0]  # 5=full, 3=partial, 0=none
        realtime_support = [0, 0, 5, 5]
        standardization = [4, 5, 4, 5]  # 5=international standard, 4=de facto standard
        eu_adoption = [4, 5, 3, 4]
        
        # Add traces for each metric
        fig.add_trace(go.Scatterpolar(
            r=static_support,
            theta=formats,
            fill='toself',
            name='Static Schedule Support',
            line=dict(color="#4dabf7"),
            fillcolor="rgba(77, 171, 247, 0.3)"
        ))
        
        fig.add_trace(go.Scatterpolar(
            r=realtime_support,
            theta=formats,
            fill='toself',
            name='Real-time Support',
            line=dict(color="#51cf66"),
            fillcolor="rgba(81, 207, 102, 0.3)"
        ))
        
        fig.add_trace(go.Scatterpolar(
            r=standardization,
            theta=formats,
            fill='toself',
            name='Standardization Level',
            line=dict(color="#fcc419"),
            fillcolor="rgba(252, 196, 25, 0.3)"
        ))
        
        fig.add_trace(go.Scatterpolar(
            r=eu_adoption,
            theta=formats,
            fill='toself',
            name='EU Adoption',
            line=dict(color="#ff6b6b"),
            fillcolor="rgba(255, 107, 107, 0.3)"
        ))
        
        # Update layout
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 5],
                    color=dark_text_color
                ),
                bgcolor=dark_paper_color
            ),
            showlegend=True,
            title="Transit Data Format Comparison",
            template="plotly_dark"
        )
    
    else:
        fig.update_layout(title="Select a data type")
    
    # Apply dark theme to all figures
    fig.update_layout(
        paper_bgcolor=dark_paper_color,
        plot_bgcolor=dark_bg_color,
        font=dict(color=dark_text_color),
    )
    
    return fig

@app.callback(
    Output('data-details', 'children'),
    Input('details-type-dropdown', 'value')
)
def update_details(data_type):
    if data_type == 'gtfs':
        gtfs_stats = overview_data.get('gtfs_stats', {})
        if gtfs_stats:
            details = []
            for file_name, file_stats in gtfs_stats.items():
                details.append(html.H4(file_name))
                
                # Parse string representation of dictionaries if needed
                file_stats = parse_string_dict(file_stats)
                
                # Now safely access dictionary attributes
                total_records = file_stats.get('total_records', 0)
                tables = file_stats.get('tables', {})
                
                details.append(html.P(f"Total records: {total_records}"))
                
                for table_name, table_info in tables.items():
                    details.append(html.H5(table_name))
                    details.append(html.P(f"Records: {table_info.get('record_count', 0)}"))
                    details.append(html.P(f"Columns: {', '.join(table_info.get('columns', []))}"))
                
                details.append(html.Hr())
                
            return details
        return html.P("No GTFS data details available")
        
    elif data_type == 'netex':
        netex_stats = overview_data.get('netex_stats', {})
        if netex_stats:
            details = []
            for file_name, stats in netex_stats.items():
                details.append(html.H4(file_name))
                
                # Parse string representation if needed
                stats = parse_string_dict(stats)
                
                for element, count in stats.items():
                    details.append(html.P(f"{element}: {count}"))
                details.append(html.Hr())
            return details
        return html.P("No NeTEx data details available")
    
    elif data_type == 'rawdata':
        rawdata_stats = overview_data.get('rawdata_stats', {})
        if rawdata_stats:
            details = []
            for file_name, stats in rawdata_stats.items():
                details.append(html.H4(file_name))
                
                # Parse string representation if needed
                stats = parse_string_dict(stats)
                
                if 'file_count' in stats:
                    details.append(html.P(f"Total files: {stats.get('file_count', 0)}"))
                
                if 'file_info' in stats:
                    file_info = parse_string_dict(stats['file_info'])
                    details.append(html.H5("File Information"))
                    for key, value in file_info.items():
                        details.append(html.P(f"{key}: {value}"))
                
                if 'file_types' in stats:
                    file_types = parse_string_dict(stats['file_types'])
                    details.append(html.H5("File Types"))
                    for ext, count in file_types.items():
                        details.append(html.P(f"{ext if ext else 'No extension'}: {count}"))
                
                details.append(html.Hr())
            return details
        return html.P("No raw data details available")
        
    elif data_type == 'realtime':
        realtime_stats = overview_data.get('realtime_stats', {})
        if realtime_stats:
            details = []
            
            for category in ['with_platform_changes', 'without_platform_changes']:
                if category in realtime_stats:
                    category_stats = realtime_stats[category]
                    
                    # Parse string representation if needed
                    category_stats = parse_string_dict(category_stats)
                    
                    if category_stats:  # Only show if there's actual data
                        details.append(html.H4(f"Real-time data {category.replace('_', ' ')}"))
                        for file_name, file_stats in category_stats.items():
                            details.append(html.P(f"File: {file_name}"))
                            
                            # Parse file stats if needed
                            file_stats = parse_string_dict(file_stats)
                            
                            for key, value in file_stats.items():
                                details.append(html.P(f"{key}: {value}"))
                            details.append(html.Hr())
            
            if not details:
                details.append(html.P("No real-time files found or sample data not loaded yet."))
                details.append(html.P("Update the data to generate sample real-time data for demonstration."))
                details.append(html.Button("Generate Sample Data", id='generate-samples-button', n_clicks=0))
                        
            return details
        return html.P("No real-time data details available")
        
    return html.P("Select a data type to see details")

@app.callback(
    Output('update-status', 'children'),
    [Input('update-button', 'n_clicks'),
     Input('generate-samples-button', 'n_clicks')] if 'generate-samples-button' in app.layout else [Input('update-button', 'n_clicks')]
)
def update_data(update_clicks, sample_clicks=0):
    ctx = callback_context
    button_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
    
    if ctx.triggered:
        try:
            analyzer = TrainDataAnalyzer()
            analyzer.load_planning_data()
            analyzer.load_realtime_data()
            new_overview = analyzer.generate_overview()
            analyzer.save_overview(new_overview)
            
            # Update the global overview_data
            global overview_data
            overview_data = new_overview
            
            action = "updated" if button_id == 'update-button' else "generated sample data and updated"
            
            return html.Div([
                html.P(f"Data {action} successfully!", style={"color": "green"}),
                html.P(f"Last update: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
            ])
        except Exception as e:
            return html.Div(f"Error updating data: {str(e)}", style={"color": "red"})
    return ""

@app.callback(
    [Output('map-iframe', 'src'),
     Output('map-status', 'children'),
     Output('map-container', 'style')],
    [Input('generate-map-button', 'n_clicks')]
)
def generate_route_map(n_clicks):
    if n_clicks is None or n_clicks == 0:
        return "", "", {"display": "none"}
    
    try:
        # Fix import by using direct import from the app directory
        from map_visualization import visualize_train_routes
        
        # Generate a unique filename based on timestamp
        import time
        map_filename = f"train_routes_{int(time.time())}.html"
        
        # Generate the map with dark mode
        map_path = visualize_train_routes(output_file=map_filename, dark_mode=True)
        
        # Get relative path for iframe src
        map_url = f"/assets/{map_filename}"
        
        # Copy the map file to the assets directory for Dash to serve it
        import shutil
        from pathlib import Path
        assets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
        Path(assets_dir).mkdir(exist_ok=True)
        shutil.copy2(map_path, os.path.join(assets_dir, map_filename))
        
        return map_url, html.P("Map generated successfully!", style={"color": "green"}), {"display": "block"}
    except Exception as e:
        return "", html.P(f"Error generating map: {str(e)}", style={"color": "red"}), {"display": "none"}

# Add server object for gunicorn deployment
server = app.server

if __name__ == '__main__':
    app.run_server(debug=True)
