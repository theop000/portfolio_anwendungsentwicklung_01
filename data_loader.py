import requests 
import os
import pandas as pd

file_url_stations = "https://www1.ncdc.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.csv"

r = requests.get(file_url_stations)
if not os.path.exists("./data/stations.csv"):
    with open("./data/stations.csv", "wb") as stations_txt:
        stations_txt.write(r.content)
    print("File 'stations.csv' successfully downloaded")
    
else:
    print("File 'stations.csv' already exists")

file_url_inventory = "https://www1.ncdc.noaa.gov/pub/data/ghcn/daily/ghcnd-inventory.txt"

r = requests.get(file_url_inventory)
if not os.path.exists("./data/stations.csv"):
    with open("./data/inventory.txt", "wb") as inventory_txt:
        inventory_txt.write(r.content)
    print("File 'inventory.txt' successfully downloaded")
    
else:
    print("File 'inventory.txt' already exists")

def download_station_data(station_id):
    """
    Downloads and converts a station's .dly file to CSV format.
    
    Args:
        station_id (str): The station ID from the stations.csv file
        
    Returns:
        bool: True if successful, False if failed
    """
    base_url = "https://www.ncei.noaa.gov/pub/data/ghcn/daily/all/"
    file_url = f"{base_url}{station_id}.dly"
    
    try:
        # Download the .dly file
        r = requests.get(file_url)
        r.raise_for_status()  # Raises an HTTPError if the status is 4xx, 5xx
        
        # Create data directory if it doesn't exist
        os.makedirs("./data/stations", exist_ok=True)
        
        # Parse the fixed-width format .dly file
        data = []
        content = r.content.decode('utf-8').split('\n')
        
        for line in content:
            if len(line) < 269:  # Skip incomplete lines
                continue
                
            station = line[0:11]
            year = int(line[11:15])
            month = int(line[15:17])
            element = line[17:21]
            
            # Process daily values (including flags)
            for day in range(31):
                pos = 21 + (day * 8)  # Each daily value takes 8 characters
                value = line[pos:pos+5]
                qflag = line[pos+5:pos+6]
                mflag = line[pos+6:pos+7]
                sflag = line[pos+7:pos+8]
                
                try:
                    value = int(value)
                    if value == -9999:  # Missing value in GHCN-Daily
                        value = None
                except ValueError:
                    value = None
                
                if value is not None:  # Only add non-missing values
                    data.append({
                        'Station_ID': station,
                        'Year': year,
                        'Month': month,
                        'Day': day + 1,
                        'Element': element,
                        'Value': value,
                        'Quality_Flag': qflag,
                        'Measurement_Flag': mflag,
                        'Source_Flag': sflag
                    })
        
        # Convert to DataFrame and save as CSV
        df = pd.DataFrame(data)
        output_file = f"./data/stations/{station_id}.csv"
        df.to_csv(output_file, index=False)
        print(f"Successfully downloaded and converted {station_id} data to CSV")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"Error downloading data for station {station_id}: {e}")
        return False
    except Exception as e:
        print(f"Error processing data for station {station_id}: {e}")
        return False
