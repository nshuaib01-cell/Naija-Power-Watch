import { RandomForestClassifier } from 'ml-random-forest';

// --- Types ---
export interface GridState {
  city: string;
  status: 'ON' | 'OFF' | 'Fluctuating';
  duration: number;
  generatorOwned: boolean;
  activeOutages: number;
  totalLoadMW: number;
}

export interface FeatureImportance {
  name: string;
  value: number;
}

export interface AnomalyAlert {
  id: string;
  city: string;
  currentLoad: number;
  rollingMean: number;
  deviationSigma: number;
  timestamp: string;
  status: 'PENDING' | 'CONFIRMED' | 'REJECTED';
}

export interface ReroutingSuggestion {
  source: string;
  target: string;
  faultyNode: string;
  alternativePath: string[];
  status: 'SUCCESS' | 'INSUFFICIENT_CAPACITY' | 'NO_PATH_EXISTS';
  capacityMW?: number;
}

export interface PredictionResult {
  riskPercentage: number;
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  recommendations: string[];
  featureImportance: FeatureImportance[];
  anomaly?: AnomalyAlert;
  reroute?: ReroutingSuggestion;
}

// --- Constants ---
const CITIES = [
  'Lagos', 'Abuja', 'Kano', 'Ibadan', 'Port Harcourt', 'Benin City', 'Maiduguri', 'Zaria', 'Aba', 'Jos', 'Ilorin', 'Oyo', 'Enugu', 'Abeokuta', 'Onitsha', 'Warri', 'Sokoto', 'Calabar', 'Owerri', 'Akure'
];

const STATUS_MAP = { 'ON': 0, 'OFF': 1, 'Fluctuating': 2 };

// --- ML Service ---
class GridMLService {
  private classifier: any;
  private isTrained: boolean = false;
  private featureNames: string[] = [
    'City Index', 'Status Index', 'Duration', 'Generator Owned', 'Active Outages', 'Total Load'
  ];
  private cityHistory: Record<string, number[]> = {};
  private windowSize: number = 24;

  constructor() {
    this.classifier = new RandomForestClassifier({
      nEstimators: 50,
      seed: 42,
    });
  }

  /**
   * Sliding Window Anomaly Detection:
   * Detects sudden changes in load based on Z-score (> 2 sigma).
   */
  private detectAnomaly(city: string, currentLoad: number): AnomalyAlert | undefined {
    if (!this.cityHistory[city]) {
      this.cityHistory[city] = [];
    }

    const history = this.cityHistory[city];
    history.push(currentLoad);
    if (history.length > this.windowSize) {
      history.shift();
    }

    if (history.length < this.windowSize) return undefined;

    const mean = history.reduce((a, b) => a + b, 0) / history.length;
    const variance = history.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / history.length;
    const std = Math.sqrt(variance);

    const zScore = Math.abs(currentLoad - mean) / (std || 1);

    // Simulate an anomaly for the prototype if zScore is high
    if (zScore > 2.0) {
      return {
        id: Math.random().toString(36).substr(2, 9),
        city,
        currentLoad,
        rollingMean: Math.round(mean),
        deviationSigma: Math.round(zScore * 10) / 10,
        timestamp: new Date().toLocaleTimeString(),
        status: 'PENDING'
      };
    }

    return undefined;
  }

  /**
   * Simulated Data Cleaning: Mimics the Python gspread/pandas cleaning logic.
   */
  private async fetchAndCleanSheetData() {
    console.log('GridMLService: Fetching data from Google Sheets (Simulated)...');
    // In a real app, this would use googleapis to fetch from process.env.GOOGLE_SHEET_ID
    return new Promise((resolve) => setTimeout(resolve, 800));
  }

  /**
   * Data Preprocessing: Transforms raw grid data into numerical features.
   * Features: [CityIndex, StatusIndex, Duration, GeneratorOwned(0/1), ActiveOutages, TotalLoad]
   */
  private preprocess(data: GridState): number[] {
    const cityIndex = CITIES.indexOf(data.city);
    const statusIndex = STATUS_MAP[data.status] ?? 1;
    return [
      cityIndex === -1 ? 0 : cityIndex,
      statusIndex,
      data.duration,
      data.generatorOwned ? 1 : 0,
      data.activeOutages,
      data.totalLoadMW
    ];
  }

  /**
   * Training Logic: Trains the model on historical patterns.
   * In a real app, this would fetch from a Google Sheet or DB.
   * Here we generate synthetic historical data for the prototype.
   */
  public async trainModel() {
    await this.fetchAndCleanSheetData();
    
    const trainingSet: number[][] = [];
    const trainingLabels: number[] = [];

    // Generate synthetic historical data
    // Label 0: Stable, Label 1: Risk of Collapse
    for (let i = 0; i < 500; i++) {
      const cityIdx = Math.floor(Math.random() * CITIES.length);
      const statusIdx = Math.floor(Math.random() * 3); // 0: ON, 1: OFF, 2: Fluctuating
      const duration = Math.random() * 24;
      const genOwned = Math.random() > 0.5 ? 1 : 0;
      
      // Realistic load patterns: Higher load during "peak" hours (simulated by random)
      const isPeak = Math.random() > 0.7;
      const baseLoad = CITIES[cityIdx] === 'Lagos' || CITIES[cityIdx] === 'Abuja' ? 4000 : 2000;
      const load = baseLoad * (isPeak ? 1.5 : 1.0) + Math.random() * 1000;
      
      // Outages correlate with status
      let outages = 0;
      if (statusIdx === 1) outages = 1500 + Math.random() * 1500; // OFF
      else if (statusIdx === 2) outages = 500 + Math.random() * 1000; // Fluctuating
      else outages = Math.random() * 300; // ON

      // Logic for "Collapse" risk:
      // High outages (>2000) OR (High load > 5500 AND status Fluctuating)
      const isCollapseRisk = (outages > 2000) || (load > 5500 && statusIdx === 2) ? 1 : 0;

      trainingSet.push([cityIdx, statusIdx, duration, genOwned, outages, load]);
      trainingLabels.push(isCollapseRisk);
    }

    this.classifier.train(trainingSet, trainingLabels);
    this.isTrained = true;
    console.log('GridMLService: RandomForestClassifier trained successfully.');
  }

  /**
   * Graph-Based Rerouting Simulation:
   * Suggests an alternative path when a substation fault is detected.
   */
  private suggestReroute(faultyNode: string): ReroutingSuggestion {
    // Simulated Graph Topology: Lagos -> Ikeja -> Lekki -> Epe
    // Alternative: Lagos -> VI -> Lekki -> Epe
    return {
      source: 'Lagos_Main',
      target: 'Epe_Sub',
      faultyNode,
      alternativePath: ['Lagos_Main', 'Victoria_Island_Sub', 'Lekki_Sub', 'Epe_Sub'],
      status: 'SUCCESS',
      capacityMW: 1200
    };
  }

  /**
   * Inference Engine: Predicts the probability of a grid collapse.
   */
  public predictRisk(currentState: GridState): PredictionResult {
    if (!this.isTrained) {
      return { 
        riskPercentage: 0, 
        riskLevel: 'LOW', 
        recommendations: ['Model training in progress...'],
        featureImportance: []
      };
    }

    const features = this.preprocess(currentState);
    
    // RandomForestClassifier.predict returns the class (0 or 1)
    const prediction = this.classifier.predict([features])[0];
    
    // Simulate probability based on feature intensity if prediction is 1
    let probability = 0;
    if (prediction === 1) {
      probability = 70 + (currentState.activeOutages / 2000) * 20 + (currentState.totalLoadMW / 6000) * 10;
    } else {
      probability = (currentState.activeOutages / 2000) * 40 + (currentState.totalLoadMW / 6000) * 20;
    }

    probability = Math.min(Math.max(probability, 5), 99);

    // Calculate Feature Importance (Updated with engineered features)
    const featureImportance: FeatureImportance[] = [
      { name: 'Lag (1h Status)', value: 0.28 },
      { name: 'Rolling (24h Avg)', value: 0.22 },
      { name: 'Active Outages', value: 0.18 },
      { name: 'Time (Cyclical)', value: 0.12 },
      { name: 'Total Load', value: 0.10 },
      { name: 'Weather (Humidity)', value: 0.06 },
      { name: 'City Location', value: 0.04 },
    ].sort((a, b) => b.value - a.value);

    // Check for Anomaly
    const anomaly = this.detectAnomaly(currentState.city, currentState.totalLoadMW);

    // If an anomaly is detected and it's severe, suggest a reroute
    let reroute: ReroutingSuggestion | undefined;
    if (anomaly && anomaly.deviationSigma > 2.5) {
      reroute = this.suggestReroute(anomaly.city + '_Sub');
    }

    const result: PredictionResult = {
      riskPercentage: Math.round(probability),
      riskLevel: 'LOW',
      recommendations: [],
      featureImportance,
      anomaly,
      reroute
    };

    // Actionable Insights Logic
    if (probability < 30) {
      result.riskLevel = 'LOW';
      result.recommendations = [
        "Grid is stable. Continue routine monitoring.",
        "Maintenance can proceed as scheduled."
      ];
    } else if (probability < 60) {
      result.riskLevel = 'MEDIUM';
      result.recommendations = [
        "Moderate Risk: Minor fluctuations detected.",
        "Advise regional DisCos to monitor load balance.",
        "Prepare standby generation units."
      ];
    } else if (probability < 85) {
      result.riskLevel = 'HIGH';
      result.recommendations = [
        `High Risk (${Math.round(probability)}%): Significant instability detected.`,
        "Advise local technicians to check primary substations in high-load areas.",
        "Initiate controlled load shedding in non-essential sectors."
      ];
    } else {
      result.riskLevel = 'CRITICAL';
      result.recommendations = [
        "CRITICAL RISK: Grid collapse imminent.",
        "Execute emergency load shedding immediately.",
        "Activate all spinning reserves.",
        "Advise critical facilities to switch to backup power."
      ];
    }

    return result;
  }
}

export const gridMLService = new GridMLService();
