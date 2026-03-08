import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

class GridFaultSimulator:
    def __init__(self, cities=['Lagos', 'Abuja', 'Kano', 'Ibadan', 'Port Harcourt']):
        self.cities = cities
        self.scenarios = [
            'NORMAL', 
            'TRANSFORMER_OVERLOAD', 
            'LINE_TRIP', 
            'CASCADING_FAILURE', 
            'WEATHER_STORM'
        ]

    def generate_scenario(self, scenario_type='NORMAL', start_time=None):
        """
        Generates a sequence of data points representing a specific fault scenario.
        """
        if start_time is None:
            start_time = datetime.now()
        
        data = []
        base_load = 3000
        
        if scenario_type == 'NORMAL':
            for i in range(10):
                data.append({
                    'timestamp': (start_time + timedelta(hours=i)).isoformat(),
                    'city': random.choice(self.cities),
                    'total_load_mw': base_load + random.randint(-200, 200),
                    'active_outages': random.randint(0, 50),
                    'weather': 'Clear',
                    'outage_occurred': 0,
                    'fault_type': 'NONE'
                })
        
        elif scenario_type == 'TRANSFORMER_OVERLOAD':
            # Gradual load increase leading to a trip
            for i in range(10):
                load = base_load + (i * 400) # Rapid increase
                outage = 1 if load > 5500 else 0
                data.append({
                    'timestamp': (start_time + timedelta(minutes=i*15)).isoformat(),
                    'city': 'Lagos',
                    'total_load_mw': load,
                    'active_outages': 50 + (i * 10),
                    'weather': 'Clear',
                    'outage_occurred': outage,
                    'fault_type': 'OVERLOAD' if outage else 'NONE'
                })

        elif scenario_type == 'CASCADING_FAILURE':
            # One city fails, pushing load to others, causing them to fail
            affected_cities = self.cities[:3]
            for i, city in enumerate(affected_cities):
                # Each subsequent city gets more load
                load = base_load + (i * 1000)
                data.append({
                    'timestamp': (start_time + timedelta(minutes=i*5)).isoformat(),
                    'city': city,
                    'total_load_mw': load,
                    'active_outages': 100 * (i + 1),
                    'weather': 'Clear',
                    'outage_occurred': 1 if i > 0 else 0,
                    'fault_type': 'CASCADE' if i > 0 else 'INITIAL_TRIP'
                })

        return pd.DataFrame(data)

    def generate_stress_test_dataset(self, num_samples=1000):
        """
        Generates a large balanced dataset for ML model training/testing.
        """
        all_data = []
        for _ in range(num_samples // 10):
            scenario = random.choice(self.scenarios)
            df = self.generate_scenario(scenario)
            all_data.append(df)
        
        final_df = pd.concat(all_data, ignore_index=True)
        # Shuffle
        final_df = final_df.sample(frac=1).reset_index(drop=True)
        return final_df

# Example Usage:
# simulator = GridFaultSimulator()
# # Generate a specific cascading failure scenario
# cascade_df = simulator.generate_scenario('CASCADING_FAILURE')
# print("--- Cascading Failure Scenario ---")
# print(cascade_df[['timestamp', 'city', 'total_load_mw', 'outage_occurred', 'fault_type']])

# # Generate a full stress-test dataset
# stress_test_df = simulator.generate_stress_test_dataset(500)
# stress_test_df.to_csv('grid_stress_test_data.csv', index=False)
# print(f"\nGenerated stress test dataset with {len(stress_test_df)} rows.")
