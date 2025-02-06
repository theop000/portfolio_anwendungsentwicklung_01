import pandas as pd
import dash
from dash import html, dcc, Input, Output, State, ctx
import plotly.express as px
import json
import numpy as np
from math import radians, sin, cos, sqrt, atan2

# Create the Dash app
app = dash.Dash(__name__)

stations_df = pd.read_csv('./data/stations_inventory.csv',
                          usecols= ['Station_Name', 'Latitude', 'Longitude'])
stations_df = stations_df.drop_duplicates(subset=['Station_Name'], keep='first')

# Create the map figure
fig = px.scatter_map(stations_df,
                       lat='Latitude',
                       lon='Longitude',
                       hover_name='Station_Name',
                       zoom=4,
                       height=800)

# Set consistent styling
fig.update_layout(
    map_style="carto-positron",              # Set consistent map style
    map=dict(
        center=dict(lat=48.0458, lon=8.4617),
    ),
    margin={"r":0,"t":0,"l":0,"b":0},
    clickmode='event+select'
)

# Set consistent marker size for all points
fig.update_traces(
    marker=dict(size=3),                        # Set all markers to size 3
    selector=dict(type='scattermapbox')
)

# Define the app layout
app.layout = html.Div([
    # Store component to save the selected stations
    dcc.Store(id='selected-stations-store'),
    # Store for button state
    dcc.Store(id='button-state', data={'active': False}),

    dcc.Tabs([
        dcc.Tab(label= 'Karte - Wetterstationen', children= [
            html.H1('Karte - Wetterstationen', 
                    style={'textAlign': 'left', 'marginBottom': 10, 'fontWeight': 'bold'}),
            
            # Flex container for map and sidebar
            html.Div([
                # Map container (left side)
                html.Div([
                    dcc.Graph(id='station-map', 
                              figure=fig,
                              config={
                                  'scrollZoom': True,
                                  'displayModeBar': False
                              }),
                    dcc.Store(id='clicked-coord', data={'lat': None, 'lon': None})
                ], style={'width': '75%', 'display': 'inline-block'}),
                
                # Sidebar container (right side)
                html.Div([
                    html.H3('Sucheinstellungen', style={'marginBottom': '20px'}),
                    
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
                    html.Label('Anzahl der Stationen', style={'fontWeight': 'bold'}),
                    dcc.Slider(id='station-count-slider', min=1, max=10, value=5, step=1),
                    html.Br(),
                    html.Br(),
                    
                    # Place Pin button moved to sidebar
                    html.Button('Pin platzieren', 
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

                    # Search Parameter container (right side)
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
        ]),
        dcc.Tab(label='Stationsdaten', children=[
            html.H1('Stationsdaten',
                    style={'textAlign': 'left', 'marginBottom': 20, 'fontWeight': 'bold'}),
            html.Div([
                html.Div(id='station-data-table')
            ])
        ])            
    ])
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
    Output('click-data', 'children'),
    Input('station-map', 'clickData'),
    prevent_initial_call=True
)
def update_click_info(clickData):
    if not clickData:
        return "Click on the map to place a pin"
    
    lat = clickData['points'][0]['lat']
    lon = clickData['points'][0]['lon']
    return f'Selected coordinates: {lat:.4f}, {lon:.4f}'

@app.callback(
    Output('station-map', 'figure'),
    Output('selected-stations-store', 'data'),
    Input('place-pin-button', 'n_clicks'),
    Input('radius-slider', 'value'),
    Input('station-count-slider', 'value'),
    State('station-map', 'clickData'),
    State('station-map', 'figure'),
    prevent_initial_call=True
)
def update_stations_selection(n_clicks, radius_value, count_value, clickData, figure):
    if not clickData:
        return figure, None
    
    # Get coordinates from click
    lat = clickData['points'][0]['lat']
    lon = clickData['points'][0]['lon']
    
    # Calculate distances and find closest stations
    stations_df['Distance'] = stations_df.apply(
        lambda row: haversine_distance(lat, lon, row['Latitude'], row['Longitude']), 
        axis=1
    )
    
    closest_stations = stations_df[stations_df['Distance'] <= radius_value].nsmallest(count_value, 'Distance')
    
    # Return unchanged figure and the station data
    return figure, closest_stations.to_dict('records')

# Add new callback for the second tab
@app.callback(
    Output('station-data-table', 'children'),
    Input('selected-stations-store', 'data'),
    prevent_initial_call=True
)
def update_station_table(stations_data):
    if not stations_data:
        return "No stations selected"
    
    # Read the full inventory file
    inventory_df = pd.read_csv('./data/stations_inventory.csv')
    
    # Convert the stored data to a DataFrame
    selected_df = pd.DataFrame(stations_data)
    
    # Merge with inventory data based on Station_ID
    merged_df = pd.merge(
        selected_df,
        inventory_df,
        on='Station_Name',
        how='left'
    )
    
    # Select and reorder columns
    display_df = merged_df[['Station_Name', 'Distance', 'Element', 'FirstYear', 'LastYear', 'Station_ID']]
    
    # Create a formatted table using dash_table
    return dash.dash_table.DataTable(
        data=display_df.to_dict('records'),
        columns=[{'name': col, 'id': col} for col in display_df.columns],
        style_table={'overflowX': 'auto'},
        style_cell={
            'textAlign': 'left',
            'padding': '10px'
        },
        style_header={
            'backgroundColor': 'rgb(230, 230, 230)',
            'fontWeight': 'bold'
        }
    )

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)