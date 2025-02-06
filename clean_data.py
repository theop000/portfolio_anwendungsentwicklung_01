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
