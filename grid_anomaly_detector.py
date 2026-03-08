import pandas as pd
import numpy as np
from collections import deque

class GridAnomalyDetector:
    def __init__(self, window_size=24, threshold_sigma=2):
        """
        Initialize the Anomaly Detector.
        :param window_size: Number of previous data points to consider for the rolling mean/std.
        :param threshold_sigma: Number of standard deviations to trigger an alert.
        """
        self.window_size = window_size
        self.threshold_sigma = threshold_sigma
        # Store history per city: { 'Lagos': deque([val1, val2, ...], maxlen=window_size) }
        self.city_history = {}
        self.pending_anomalies = []

    def process_reading(self, city, current_load):
        """
        Process a single incoming reading and check for anomalies.
        """
        if city not in self.city_history:
            self.city_history[city] = deque(maxlen=self.window_size)
            self.city_history[city].append(current_load)
            return None # Not enough data yet

        history = list(self.city_history[city])
        
        if len(history) < self.window_size:
            self.city_history[city].append(current_load)
            return None

        # Calculate rolling statistics
        mean = np.mean(history)
        std = np.std(history)
        
        # Avoid division by zero if std is 0
        if std == 0:
            std = 1e-6

        # Check for deviation (Z-Score)
        z_score = abs(current_load - mean) / std
        
        is_anomaly = z_score > self.threshold_sigma
        
        # Update history
        self.city_history[city].append(current_load)

        if is_anomaly:
            anomaly_data = {
                'city': city,
                'current_load': current_load,
                'rolling_mean': round(mean, 2),
                'deviation_sigma': round(z_score, 2),
                'status': 'PENDING_VALIDATION'
            }
            self.pending_anomalies.append(anomaly_data)
            return anomaly_data
        
        return None

    def validate_anomaly(self, anomaly_id, operator_confirmed):
        """
        Human-in-the-Loop Validation Step.
        """
        # In a real app, anomaly_id would be a database ID
        # For this module, we'll just process the most recent one
        if not self.pending_anomalies:
            return "No pending anomalies to validate."

        anomaly = self.pending_anomalies.pop(0)
        
        if operator_confirmed:
            anomaly['status'] = 'CONFIRMED'
            return self.suggest_rerouting(anomaly)
        else:
            anomaly['status'] = 'REJECTED'
            return "Anomaly rejected by operator. No action taken."

    def suggest_rerouting(self, anomaly):
        """
        Logic for suggesting a rerouting action after confirmation.
        """
        return f"ALERT CONFIRMED for {anomaly['city']}. Suggested Action: Initiate load rerouting from Substation A to Substation B to balance the {anomaly['deviation_sigma']} sigma deviation."

# --- Human-in-the-Loop (HITL) Implementation Guide ---
# 1. Detection: The 'process_reading' function identifies a statistical outlier.
# 2. Alerting: The system pushes this anomaly to a 'Pending Queue' and notifies the operator via a dashboard UI.
# 3. UI Interaction: The operator sees the 'Anomaly Alert' with the Z-score and rolling mean context.
# 4. Decision: The operator clicks 'Confirm' or 'Dismiss' based on their domain knowledge (e.g., they know a festival is happening, so high load is expected).
# 5. Execution: Only if 'Confirm' is clicked does the system trigger the 'suggest_rerouting' or automated control logic.

# Example Usage:
# detector = GridAnomalyDetector(window_size=10, threshold_sigma=2)
# # Simulate normal load
# for _ in range(10): detector.process_reading('Lagos', 4000 + np.random.randint(-100, 100))
# # Simulate sudden spike
# alert = detector.process_reading('Lagos', 5500)
# if alert:
#     print(f"Anomaly Detected: {alert}")
#     # HITL Step
#     action = detector.validate_anomaly(0, operator_confirmed=True)
#     print(f"Operator Action: {action}")
