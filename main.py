import pandas as pd
import dash
from dash import html, dcc, Input, Output, State, ctx
import plotly.express as px
import json
import numpy as np
from math import radians, sin, cos, sqrt, atan2

# Create the Dash app
app = dash.Dash(__name__)

stations_df = pd.read_csv('./data/stations.csv',
                          usecols=['Station_Name', 'Latitude', 'Longitude', 'FirstYear', 'LastYear', 'Station_ID'])


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
                    
                    # Radius input
                    html.Label('Suchradius (max. 100km)', style={'fontWeight': 'bold'}),
                    dcc.Input(
                        id='radius-slider',  
                        type='number',
                        min=1,
                        max=100,
                        value=50,
                        step=1,
                        style={
                            'width': '100%',
                            'padding': '8px',
                            'marginTop': '5px',
                            'marginBottom': '10px',
                            'borderRadius': '4px',
                            'border': '1px solid #ccc'
                        }
                    ),
                    html.Br(),
                    
                    # Station count slider
                    html.Label('Anzahl der Stationen', style={'fontWeight': 'bold'}),
                    dcc.Slider(id='station-count-slider', min=1, max=10, value=5, step=1),
                    html.Br(),
                    
                    # Year range selection
                    html.Label('Zeitraum auswählen', style={'fontWeight': 'bold'}),
                    html.Div([
                        # Left input (Von)
                        html.Div([
                            dcc.Input(
                                id='year-from',
                                type='number',
                                min=0,
                                value=2000,
                                step=1,
                                style={
                                    'width': '100%',
                                    'padding': '8px',
                                    'borderRadius': '4px',
                                    'border': '1px solid #ccc'
                                }
                            ),
                            html.Label('Von', style={
                                'fontSize': '12px',
                                'color': '#666',
                                'marginTop': '4px'
                            })
                        ], style={'width': '48%', 'display': 'inline-block'}),
                        
                        # Right input (Bis)
                        html.Div([
                            dcc.Input(
                                id='year-to',
                                type='number',
                                min=2000,
                                max=2024,
                                value=2024,
                                step=1,
                                style={
                                    'width': '100%',
                                    'padding': '8px',
                                    'borderRadius': '4px',
                                    'border': '1px solid #ccc'
                                }
                            ),
                            html.Label('Bis', style={
                                'fontSize': '12px',
                                'color': '#666',
                                'marginTop': '4px'
                            })
                        ], style={'width': '48%', 'display': 'inline-block', 'marginLeft': '4%'})
                    ]),
                    html.Br(),                    
                    
                    # Coordinate inputs
                    html.Label('Koordinaten eingeben', style={'fontWeight': 'bold'}),
                    html.Div([
                        # Left input (Breitengrad)
                        html.Div([
                            dcc.Input(
                                id='latitude-input',
                                type='number',
                                value=48.0458,
                                min=-90,
                                max=90,
                                style={
                                    'width': '100%',
                                    'padding': '8px',
                                    'borderRadius': '4px',
                                    'border': '1px solid #ccc'
                                }
                            ),
                            html.Label('Breitengrad', style={
                                'fontSize': '12px',
                                'color': '#666',
                                'marginTop': '4px'
                            })
                        ], style={'width': '48%', 'display': 'inline-block'}),
                        
                        # Right input (Längengrad)
                        html.Div([
                            dcc.Input(
                                id='longitude-input',
                                type='number',
                                value=8.4617,
                                min=-180,
                                max=180,
                                style={
                                    'width': '100%',
                                    'padding': '8px',
                                    'borderRadius': '4px',
                                    'border': '1px solid #ccc'
                                }
                            ),
                            html.Label('Längengrad', style={
                                'fontSize': '12px',
                                'color': '#666',
                                'marginTop': '4px'
                            })
                        ], style={'width': '48%', 'display': 'inline-block', 'marginLeft': '4%'})
                    ]),
                    html.Br(),                    

                    html.Button('Stationen suchen', 
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
    Output('latitude-input', 'value'),
    Output('longitude-input', 'value'),
    Input('station-map', 'clickData'),
    prevent_initial_call=True
)
def update_click_info(clickData):
    if not clickData:
        return "Click on the map to place a pin", 48.0458, 8.4617
    
    lat = clickData['points'][0]['lat']
    lon = clickData['points'][0]['lon']
    return f'Selected coordinates: {lat:.4f}, {lon:.4f}', lat, lon

@app.callback(
    Output('station-map', 'figure'),
    Output('selected-stations-store', 'data'),
    Input('place-pin-button', 'n_clicks'),
    Input('radius-slider', 'value'),
    Input('station-count-slider', 'value'),
    Input('year-from', 'value'),
    Input('year-to', 'value'),
    State('latitude-input', 'value'),
    State('longitude-input', 'value'),
    State('station-map', 'figure'),
    prevent_initial_call=False
)
def update_stations_selection(n_clicks, radius_value, count_value, year_from, year_to, lat, lon, figure):
    # Handle the initial call
    if n_clicks is None:
        # Calculate initial stations based on default coordinates
        stations_df['Distance'] = stations_df.apply(
            lambda row: haversine_distance(lat, lon, row['Latitude'], row['Longitude']), 
            axis=1
        )
        
        filtered_stations = stations_df[
            (stations_df['FirstYear'] <= year_to) & 
            (stations_df['LastYear'] >= year_from) &
            (stations_df['Distance'] <= radius_value)
        ].nsmallest(count_value, 'Distance')
        
        return figure, filtered_stations.to_dict('records')
    
    # Rest of the function remains the same
    stations_df['Distance'] = stations_df.apply(
        lambda row: haversine_distance(lat, lon, row['Latitude'], row['Longitude']), 
        axis=1
    )
    
    filtered_stations = stations_df[
        (stations_df['FirstYear'] <= year_to) & 
        (stations_df['LastYear'] >= year_from) &
        (stations_df['Distance'] <= radius_value)
    ].nsmallest(count_value, 'Distance')
    
    return figure, filtered_stations.to_dict('records')

@app.callback(
    Output('station-data-table', 'children'),
    Input('selected-stations-store', 'data'),
    prevent_initial_call=False
)
def update_station_table(selected_stations):
    if not selected_stations:
        return "No stations selected"
    
    # Convert stored data directly to DataFrame
    display_df = pd.DataFrame(selected_stations)[
        ['Station_Name', 'Distance', 'FirstYear', 'LastYear', 'Station_ID']
    ]
    
    # Round Distance to 2 decimal places
    display_df['Distance'] = display_df['Distance'].round(2)
    
    return dash.dash_table.DataTable(
        data=display_df.to_dict('records'),
        columns=[
            {'name': 'Station Name', 'id': 'Station_Name'},
            {'name': 'Distance (km)', 'id': 'Distance'},
            {'name': 'First Year', 'id': 'FirstYear'},
            {'name': 'Last Year', 'id': 'LastYear'},
            {'name': 'Station ID', 'id': 'Station_ID'}
        ],
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

@app.callback(
    Output('year-to', 'value'),
    Output('year-from', 'value'),
    Input('year-from', 'value'),
    Input('year-to', 'value'),
    prevent_initial_call=True
)
def validate_years(year_from, year_to):
    triggered_id = ctx.triggered_id
    
    # Ensure values are valid
    year_from = max(0, min(2024, year_from if year_from else 0)) 
    year_to = max(0, min(2024, year_to if year_to else 2024))
    
    # If "from" year was changed
    if triggered_id == 'year-from':
        if year_from > year_to:
            year_to = year_from
    # If "to" year was changed
    elif triggered_id == 'year-to':
        if year_to < year_from:
            year_from = year_to
            
    return year_to, year_from

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)