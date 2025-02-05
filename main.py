import pandas as pd
import dash
from dash import html, dcc, Input, Output, State, ctx
import plotly.express as px
import json
import numpy as np
from math import radians, sin, cos, sqrt, atan2

# Read the countries file
countries_df = pd.read_fwf('./data/countries.txt', 
                          colspecs=[(0, 2), (3, 50)],
                          names=['Code', 'Country'],
                          encoding='utf-8')

# Read the stations file with specific columns
stations_df = pd.read_csv('./data/stations.csv', 
                         usecols=[0, 1, 2, 5],  # Select first 4 columns
                         names=['Station_ID', 'Latitude', 'Longitude', 'Name'])

# Clean station names to keep only the first name before any comma
stations_df['Name'] = stations_df['Name'].str.split(',').str[0]

# Read the inventory file
inventory_df = pd.read_fwf('./data/inventory.txt',
                          colspecs=[(0, 11),    # Station ID
                                  (11, 20),     # Latitude
                                  (20, 30),     # Longitude
                                  (31, 35),     # Element
                                  (36, 40),     # First year
                                  (41, 45)],    # Last year
                          names=['Station_ID', 'Latitude', 'Longitude', 
                                'Element', 'FirstYear', 'LastYear'])

# Filter for TMAX and TMIN
temp_stations = inventory_df[inventory_df['Element'].isin(['TMAX', 'TMIN'])]

# Get unique station IDs that have both TMAX and TMIN
valid_stations = temp_stations.groupby('Station_ID').Element.nunique()
valid_station_ids = valid_stations[valid_stations == 2].index

# Filter stations_df to only include stations with both TMAX and TMIN
stations_df = stations_df[stations_df['Station_ID'].isin(valid_station_ids)]

# Create the Dash app
app = dash.Dash(__name__)

# Create the map figure
fig = px.scatter_map(stations_df,
                       lat='Latitude',
                       lon='Longitude',
                       hover_name='Name',
                       zoom=1,
                       height=800)

fig.update_layout(
    mapbox_style="open-street-map",
    margin={"r":0,"t":0,"l":0,"b":0},
    clickmode='event+select'
)

# Define the app layout
app.layout = html.Div([
    html.H1('Karte - Wetterstationen', 
            style={'textAlign': 'left', 'marginBottom': 20, 'fontWeight': 'bold'}),
    
    # Flex container for map and sidebar
    html.Div([
        # Map container (left side)
        html.Div([
            dcc.Graph(id='station-map', figure=fig),
            dcc.Store(id='clicked-coord', data={'lat': None, 'lon': None})
        ], style={'width': '75%', 'display': 'inline-block'}),
        
        # Sidebar container (right side)
        html.Div([
            html.H3('Search Settings', style={'marginBottom': '20px'}),
            
            # Radius slider
            html.Label('Suchradius (km)', style={'fontWeight': 'bold'}),
            dcc.Slider(
                id='radius-slider',
                min=1,
                max=100,
                value=50,
                step=1,
                marks={
                    1: '1',
                    25: '25',
                    50: '50',
                    75: '75',
                    100: '100'
                }
            ),
            html.Br(),
            
            # Station count slider
            html.Label('Number of Stations', style={'fontWeight': 'bold'}),
            dcc.Slider(id='station-count-slider', min=1, max=10, value=5, step=1),
            html.Br(),
            html.Br(),
            
            # Place Pin button moved to sidebar
            html.Button('Place Pin', 
                       id='place-pin-button',
                       style={
                           'width': '100%',
                           'padding': '10px',
                           'backgroundColor': '#4CAF50',
                           'color': 'white',
                           'border': 'none',
                           'borderRadius': '1px',
                           'cursor': 'pointer'
                       }),
            
            # Display clicked coordinates
            html.Div(id='click-data', 
                    style={'marginTop': '20px', 'textAlign': 'center'})
            
        ], style={
            'width': '23%',
            'display': 'inline-block',
            'verticalAlign': 'top',
            'padding': '20px',
            'backgroundColor': '#f9f9f9',
            'borderLeft': '1px solid #ccc',
            'height': '800px',
            'marginLeft': '2%'
        })
    ], style={'display': 'flex', 'flexDirection': 'row', 'justifyContent': 'space-between'})
])

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth's radius in kilometers
    
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

@app.callback(
    Output('station-map', 'figure'),
    Output('click-data', 'children'),
    Input('station-map', 'clickData'),
    Input('place-pin-button', 'n_clicks'),
    Input('radius-slider', 'value'),
    Input('station-count-slider', 'value'),
    State('station-map', 'figure'),
    prevent_initial_call=True
)
def update_map(clickData, n_clicks, radius, station_count, current_fig):
    if not ctx.triggered_id:
        return current_fig, "Click on the map to place a pin"
    
    if clickData is None:
        return current_fig, "Click on the map to place a pin"
    
    lat = clickData['points'][0]['lat']
    lon = clickData['points'][0]['lon']
    
    if ctx.triggered_id == 'place-pin-button' and clickData:
        # Calculate distances for all stations
        stations_df['Distance'] = stations_df.apply(
            lambda row: haversine_distance(lat, lon, row['Latitude'], row['Longitude']), 
            axis=1
        )
        
        # Get closest stations within radius and limit
        closest_stations = stations_df[stations_df['Distance'] <= radius].nsmallest(station_count, 'Distance')
        
        # Create new figure with base stations
        new_fig = px.scatter_mapbox(stations_df,
                                  lat='Latitude',
                                  lon='Longitude',
                                  hover_name='Name',
                                  zoom=1,
                                  height=800)
        
        # Add user pin
        new_fig.add_trace({
            'type': 'scattermap',
            'lat': [lat],
            'lon': [lon],
            'mode': 'markers',
            'marker': {'size': 1, 'color': 'red'},
            'name': 'Selected Point'
        })
        
        # Add this line to make pins smaller
        new_fig.update_traces(marker={'size': 1})
        
        new_fig.update_layout(
            mapbox_style="open-street-map",
            margin={"r":0,"t":0,"l":0,"b":0}
        )
        
        return new_fig, f'Found {len(closest_stations)} stations within {radius}km'
    
    return current_fig, f'Selected coordinates: {lat:.4f}, {lon:.4f}'

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)

