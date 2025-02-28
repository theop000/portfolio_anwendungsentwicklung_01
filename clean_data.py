import pandas as pd
import os.path

# The 'clean_data.py' script is using the files downloaded from the 'data_loader.py' script
# Firstly the files get converted, any unnecessary rows get filtered so only relevant
# stations will be used. Only stations with TMAX and TMIN data are needed.
# Upon creating the final file 'stations_inventory.csv' the temporary files will be removed



# Check if stations_inventory_merge.csv already exists
if not os.path.isfile('./data/stations_inventory.csv'):
    # Read the inventory file using space separator instead of fixed width
    inventory_df = pd.read_csv('./data/inventory.txt', 
                              sep=r'\s+',            # Using raw string for whitespace separator
                              usecols=[0, 1, 2, 3, 4, 5],
                              names=['Station_ID', 'Latitude', 'Longitude', 'Element', 'FirstYear', 'LastYear'])

    # Filter rows to keep only TMAX and TMIN elements
    inventory_df = inventory_df[inventory_df['Element'].isin(['TMAX', 'TMIN'])]

    # Display the first 5 rows of the filtered DataFrame
    print("\nFirst 5 rows of the filtered inventory data:")
    print("=" * 70)
    print(inventory_df.head().to_string())
    print("=" * 70)

    # Save the filtered DataFrame to CSV
    inventory_df.to_csv('./data/clean_inventory.csv', index=False)
    print("\nSaved filtered data to clean_inventory.csv")
else:
    print("\nstations_inventory.csv already exists. Skipping processing.")




# Check if stations_inventory_merge.csv already exists
if not os.path.isfile('./data/stations_inventory.csv'):
    # Read the clean inventory file
    clean_inventory_df = pd.read_csv('./data/clean_inventory.csv')

    # Read the stations file
    stations_names_df = pd.read_csv('./data/stations.csv', 
                                   usecols=[0, 5],  # Only need Station_ID and Station_Name (column 5)
                                   names=['Station_ID', 'Station_Name'])

    # Merge the dataframes on Station_ID
    stations_merge_df = pd.merge(stations_names_df, 
                          clean_inventory_df, 
                          on='Station_ID', 
                          how='left')
    
    

    # Save to new CSV file
    stations_merge_df.to_csv('./data/relevant_stations.csv', index=False)

    print("\nSaved relevant stations data to relevant_stations.csv")
else:
    print("\nstations_inventory.csv already exists. Skipping processing.")





# Check if stations_inventory_merge.csv already exists
if not os.path.isfile('./data/stations_inventory.csv'):
    # Read the clean_inventory.csv file
    clean_inventory_df = pd.read_csv('./data/clean_inventory.csv')
    # Read the relevant_stations.csv file
    relevant_stations_df = pd.read_csv('./data/relevant_stations.csv',
                                    usecols= ['Station_ID', 'Station_Name'])

    stations_inventory_merge_df = pd.merge(clean_inventory_df,
                                           relevant_stations_df,
                                           on='Station_ID',
                                           how='left')

    stations_inventory_merge_df = stations_inventory_merge_df.drop_duplicates(subset=['Station_ID', 'Element'])



    # Save the merged DataFrame to CSV
    stations_inventory_merge_df.to_csv('./data/stations_inventory.csv', index=False)
    print("\nSaved filtered data to stations_inventory.csv")
    os.remove('./data/inventory.txt')
    print("\nremoved temporary file inventory.txt")
    os.remove('./data/clean_inventory.csv')
    print("\nremoved temporary file clean_inventory.csv")
    os.remove('./data/stations.csv')
    print("\nremoved temporary file stations.csv")
    os.remove('./data/relevant_stations.csv')
    print("\nremoved temporary file relevant_stations.csv")
else:
    print("\nstations_inventory.csv already exists. Skipping processing.")

if not os.path.isfile('./data/stations.csv'):
    # Read the stations inventory file
    stations_inventory_df = pd.read_csv('./data/stations_inventory.csv',
                                      usecols=['Station_ID', 'Latitude', 'Longitude', 'FirstYear', 'LastYear', 'Station_Name'])
    
    # Group by Station_ID and aggregate the data
    stations_df = stations_inventory_df.groupby('Station_ID').agg({
        'Latitude': 'first',  # Take first value since it is the same for each station
        'Longitude': 'first', # Take first value since it is the same for each station
        'FirstYear': 'max',   # Take the highest FirstYear
        'LastYear': 'min',    # Take the lowest LastYear
        'Station_Name': 'first' # Take first value since it is the same for each station
    }).reset_index()

    # Save the aggregated data to stations.csv
    stations_df.to_csv('./data/stations.csv', index=False)
    print("\nSaved aggregated station data to stations.csv")
    os.remove('./data/stations_inventory.csv')
    print("\nremoved temporary file stations_inventory.csv")

def clean_station_data(station_id):
    """
    Cleans the station data by:
    1. Filtering for TMAX and TMIN elements
    2. Converting temperature from tenths of °C to °C with 2 decimal places
    3. Removing flag columns
    
    Args:
        station_id (str): The station ID to clean data for
        
    Returns:
        bool: True if successful, False if failed
    """
    try:
        # Read the CSV file
        input_file = f"./data/stations/{station_id}.csv"
        df = pd.read_csv(input_file)
        
        # Filter for TMAX and TMIN elements
        df = df[df['Element'].isin(['TMAX', 'TMIN'])]
        
        # Convert temperature from tenths of degrees to degrees Celsius
        df['Value'] = df['Value'].apply(lambda x: round(x / 10.0, 2))
        
        # Remove flag columns
        df = df.drop(['Quality_Flag', 'Measurement_Flag', 'Source_Flag'], axis=1)
        
        # Save the cleaned data back to CSV
        df.to_csv(input_file, index=False)
        print(f"Successfully cleaned data for station {station_id}")
        return True
        
    except Exception as e:
        print(f"Error cleaning data for station {station_id}: {e}")
        return False


def create_monthly_averages(station_id):
    """
    Creates a new CSV file with monthly averages for TMAX and TMIN values.
    The new file will be named 'station_id_monthly.csv'.
    
    Args:
        station_id (str): The station ID to process
        
    Returns:
        bool: True if successful, False if failed
    """
    try:
        # Read the cleaned station data
        input_file = f"./data/stations/{station_id}.csv"
        df = pd.read_csv(input_file)
        
        # Group by Year, Month, and Element to calculate monthly averages
        monthly_df = df.groupby(['Year', 'Month', 'Element'])['Value'].mean().round(2).reset_index()
        
        # Pivot the data to have TMAX and TMIN as separate columns
        monthly_df = monthly_df.pivot(
            index=['Year', 'Month'],
            columns='Element',
            values='Value'
        ).reset_index()
        
        # Rename columns to be more descriptive
        monthly_df.columns.name = None
        
        # Add Station_ID column
        monthly_df['Station_ID'] = station_id
        
        # Reorder columns to put Station_ID first
        monthly_df = monthly_df[['Station_ID', 'Year', 'Month', 'TMAX', 'TMIN']]
        
        # Save to new CSV file
        output_file = f"./data/stations/{station_id}_monthly.csv"
        monthly_df.to_csv(output_file, index=False)
        print(f"Successfully created monthly averages for station {station_id}")
        return True
        
    except Exception as e:
        print(f"Error creating monthly averages for station {station_id}: {e}")
        return False



def create_yearly_averages(station_id):
    """
    Creates a new CSV file with yearly averages for TMAX and TMIN values,
    calculated from the monthly averages.
    The new file will be named 'station_id_yearly.csv'.
    
    Args:
        station_id (str): The station ID to process
        
    Returns:
        bool: True if successful, False if failed
    """
    try:
        # Read the monthly averages file
        input_file = f"./data/stations/{station_id}_monthly.csv"
        monthly_df = pd.read_csv(input_file)
        
        # Group by Year to calculate yearly averages
        yearly_df = monthly_df.groupby(['Year']).agg({
            'Station_ID': 'first',  # Keep the station ID
            'TMAX': 'mean',         # Average of monthly TMAX values
            'TMIN': 'mean'          # Average of monthly TMIN values
        }).round(2)
        
        # Reset index to make Year a column
        yearly_df = yearly_df.reset_index()
        
        # Reorder columns
        yearly_df = yearly_df[['Station_ID', 'Year', 'TMAX', 'TMIN']]
        
        # Save to new CSV file
        output_file = f"./data/stations/{station_id}_yearly.csv"
        yearly_df.to_csv(output_file, index=False)
        print(f"Successfully created yearly averages for station {station_id}")
        return True
        
    except Exception as e:
        print(f"Error creating yearly averages for station {station_id}: {e}")
        return False
