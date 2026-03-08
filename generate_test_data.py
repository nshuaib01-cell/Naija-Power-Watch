import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def generate_synthetic_grid_data(num_records=1000):
    """
    Generates a synthetic dataset for the Smart Grid Reliability platform.
    """
    cities = [
        'Lagos', 'Abuja', 'Kano', 'Ibadan', 'Port Harcourt', 
        'Benin City', 'Maiduguri', 'Zaria', 'Aba', 'Jos'
    ]
    
    city_coords = {
        'Lagos': (6.5244, 3.3792),
        'Abuja': (9.0765, 7.3986),
        'Kano': (12.0022, 8.5920),
        'Ibadan': (7.3775, 3.9470),
        'Port Harcourt': (4.8156, 7.0498),
        'Benin City': (6.3350, 5.6037),
        'Maiduguri': (11.8311, 13.1509),
        'Zaria': (11.0691, 7.7138),
        'Aba': (5.1066, 7.3667),
        'Jos': (9.8965, 8.8583)
    }

    statuses = ['ON', 'OFF', 'Fluctuating']
    hazards_list = ['Downed Power Line', 'Sparking Transformer', 'Visible Tree Damage', 'Flooding', 'None']
    neighbor_statuses = ['on', 'off', 'unknown']

    data = []
    start_time = datetime.now() - timedelta(days=30)

    for i in range(num_records):
        city = random.choice(cities)
        lat, lon = city_coords[city]
        
        # Add slight jitter to coordinates
        lat += random.uniform(-0.05, 0.05)
        lon += random.uniform(-0.05, 0.05)
        
        timestamp = start_time + timedelta(minutes=random.randint(0, 43200)) # Over 30 days
        status = random.choices(statuses, weights=[0.7, 0.2, 0.1])[0]
        
        # Logic for load and outages
        base_load = 3000 if city in ['Lagos', 'Abuja'] else 1500
        hour = timestamp.hour
        # Peak hours 18:00 - 22:00
        peak_multiplier = 1.5 if 18 <= hour <= 22 else 1.0
        total_load = base_load * peak_multiplier + random.uniform(-500, 500)
        
        if status == 'OFF':
            outages = random.randint(1000, 3000)
            duration = random.uniform(1, 12)
        elif status == 'Fluctuating':
            outages = random.randint(200, 1000)
            duration = random.uniform(0.5, 4)
        else:
            outages = random.randint(0, 200)
            duration = random.uniform(1, 48)

        gen_owned = random.random() > 0.4
        hazards = random.sample(hazards_list, random.randint(1, 2))
        if 'None' in hazards and len(hazards) > 1:
            hazards.remove('None')
        
        neighbor_status = random.choice(neighbor_statuses)

        data.append({
            'Timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'City': city,
            'Latitude': round(lat, 6),
            'Longitude': round(lon, 6),
            'Status': status,
            'Duration_Hrs': round(duration, 2),
            'GeneratorOwned': gen_owned,
            'ActiveOutages': outages,
            'TotalLoadMW': round(total_load, 2),
            'Hazards': ', '.join(hazards),
            'NeighborStatus': neighbor_status
        })

    df = pd.DataFrame(data)
    df = df.sort_values('Timestamp')
    
    filename = 'synthetic_grid_data.csv'
    df.to_csv(filename, index=False)
    print(f"Successfully generated {num_records} records in {filename}")
    return filename

if __name__ == "__main__":
    generate_synthetic_grid_data(2000)
