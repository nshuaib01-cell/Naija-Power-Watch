import gspread
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder
from sklearn.model_selection import train_test_split
import plotly.express as px
from google.oauth2.service_account import Credentials

class NaijaGridML:
    def __init__(self, sheet_id, credentials_path):
        """
        Initialize the ML Backend with Google Sheets integration.
        """
        self.scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        self.creds = Credentials.from_service_account_file(credentials_path, scopes=self.scope)
        self.client = gspread.authorize(self.creds)
        self.sheet = self.client.open_by_key(sheet_id).sheet1
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.encoder = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
        self.is_trained = False

    def clean_data(self):
        """
        Data Cleaning & Advanced Feature Engineering:
        - Handles missing values
        - Creates Lag Features (1h, 3h)
        - Implements Rolling Window Statistics (24h)
        - Cyclical Encoding for Time (Sine/Cosine)
        - Categorical Encoding
        """
        # Read data from Google Sheet
        data = self.sheet.get_all_records()
        df = pd.DataFrame(data)

        # Handle missing values
        df = df.fillna(method='ffill').fillna(0)

        # Ensure timestamp is datetime and sorted for time-series features
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')

            # 1. Cyclical Encoding for 'hour' and 'day_of_week'
            df['hour'] = df['timestamp'].dt.hour
            df['day_of_week'] = df['timestamp'].dt.dayofweek
            
            df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
            df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
            df['day_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
            df['day_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)

            # 2. Lag Features (1-hour and 3-hour lags for outage status)
            if 'outage_occurred' in df.columns:
                df['outage_lag_1h'] = df['outage_occurred'].shift(1).fillna(0)
                df['outage_lag_3h'] = df['outage_occurred'].shift(3).fillna(0)

            # 3. Rolling Window Statistics (24-hour average outage frequency)
            if 'outage_occurred' in df.columns:
                df['outage_rolling_24h'] = df['outage_occurred'].rolling(window=24, min_periods=1).mean()

        # 4. External Metadata Integration (Weather Patterns)
        # If humidity/wind_speed exist, we ensure they are numeric
        for col in ['humidity', 'wind_speed', 'temperature']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # Categorical Encoding
        categorical_cols = ['city', 'weather', 'disco']
        existing_cat_cols = [col for col in categorical_cols if col in df.columns]
        
        if existing_cat_cols:
            encoded_cats = self.encoder.fit_transform(df[existing_cat_cols])
            encoded_df = pd.DataFrame(encoded_cats, columns=self.encoder.get_feature_names_out(existing_cat_cols))
            df = pd.concat([df.drop(existing_cat_cols, axis=1), encoded_df], axis=1)

        return df

    def train_model(self):
        """
        Model Training: Trains a RandomForestClassifier to predict 'outage_occurred'.
        """
        df = self.clean_data()
        
        if 'outage_occurred' not in df.columns:
            raise ValueError("Target column 'outage_occurred' not found in data.")

        # Define features and target
        X = df.drop(['outage_occurred', 'timestamp'], axis=1, errors='ignore')
        y = df['outage_occurred']

        # Split and train
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        self.model.fit(X_train, y_train)
        self.is_trained = True
        self.feature_names = X.columns
        
        print(f"Model trained with accuracy: {self.model.score(X_test, y_test):.2f}")

    def get_risk_score(self, live_data_row):
        """
        Risk Scoring: Returns a 'Grid Collapse Probability' as a percentage.
        Now supports cyclical time features and lag placeholders.
        """
        if not self.is_trained:
            self.train_model()

        # Preprocess live row
        live_df = pd.DataFrame([live_data_row])
        
        # Add cyclical features if hour/day provided
        if 'hour' in live_df.columns:
            live_df['hour_sin'] = np.sin(2 * np.pi * live_df['hour'] / 24)
            live_df['hour_cos'] = np.cos(2 * np.pi * live_df['hour'] / 24)
        if 'day_of_week' in live_df.columns:
            live_df['day_sin'] = np.sin(2 * np.pi * live_df['day_of_week'] / 7)
            live_df['day_cos'] = np.cos(2 * np.pi * live_df['day_of_week'] / 7)

        # Handle encoding for live data
        categorical_cols = ['city', 'weather', 'disco']
        existing_cat_cols = [col for col in categorical_cols if col in live_df.columns]
        if existing_cat_cols:
            encoded_cats = self.encoder.transform(live_df[existing_cat_cols])
            encoded_df = pd.DataFrame(encoded_cats, columns=self.encoder.get_feature_names_out(existing_cat_cols))
            live_df = pd.concat([live_df.drop(existing_cat_cols, axis=1), encoded_df], axis=1)

        # Ensure all training features are present (including lags/rolling)
        for col in self.feature_names:
            if col not in live_df.columns:
                live_df[col] = 0
        
        live_df = live_df[self.feature_names]

        # Get probability
        prob = self.model.predict_proba(live_df)[0][1]
        return round(prob * 100, 2)

    def plot_feature_importance(self):
        """
        Feature Importance: Generates a Plotly bar chart of contributing factors.
        """
        if not self.is_trained:
            return None

        importances = self.model.feature_importances_
        feat_importances = pd.Series(importances, index=self.feature_names)
        feat_importances = feat_importances.sort_values(ascending=False).head(10)

        fig = px.bar(
            feat_importances, 
            x=feat_importances.values, 
            y=feat_importances.index,
            orientation='h',
            title='Top Factors Contributing to Grid Instability',
            labels={'x': 'Importance Score', 'index': 'Factor'},
            color=feat_importances.values,
            color_continuous_scale='Viridis'
        )
        fig.show()
        return fig

    def get_recommendation(self, risk_score):
        """
        Recommendation Logic: Returns specific text based on risk score.
        """
        if risk_score < 20:
            return "Low Risk: Grid is stable. Continue routine monitoring."
        elif risk_score < 50:
            return "Moderate Risk: Minor fluctuations detected. Advise regional DisCos to monitor load balance."
        elif risk_score < 80:
            return f"High Risk ({risk_score}%): Significant instability. Advise local technicians to check primary substations in high-load areas."
        else:
            return "CRITICAL RISK: Grid collapse imminent. Execute emergency load shedding and activate all spinning reserves."

# Example Usage:
# backend = NaijaGridML(sheet_id='YOUR_SHEET_ID', credentials_path='credentials.json')
# backend.train_model()
# risk = backend.get_risk_score({'city': 'Lagos', 'hour': 14, 'weather': 'Stormy', 'disco': 'EKEDC'})
# print(f"Risk: {risk}%")
# print(f"Action: {backend.get_recommendation(risk)}")
# backend.plot_feature_importance()
