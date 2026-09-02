import axios from 'axios';

// Since Vite proxy isn't set up yet, point directly to the backend URL
// Fastapi runs on 8000 by default. If running locally, assume 8000.
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 10000,
});

export interface PredictionDetail {
  value: number;
  model_used: string;
  artifact_version: string;
  rmse_test_error: number | null;
}

export interface RiskResponse {
  category: string;
  description: string;
}

export interface ModelScope {
  validation_region: string;
  status: string;
  warning: string | null;
}

export interface CurrentWeather {
  temp_c?: number;
  rh_pct?: number;
  wind_ms?: number;
  pressure_hpa?: number;
  ghi_wm2?: number;
}

export interface ForecastResponse {
  location: {
    latitude: number;
    longitude: number;
  };
  input_timestamp: string;
  forecast_horizon_hours: number;
  prediction: {
    wbgt: PredictionDetail;
    utci: PredictionDetail;
    hi: PredictionDetail;
  };
  risk: {
    wbgt: RiskResponse;
    utci: RiskResponse;
    hi: RiskResponse;
  };
  model_scope: ModelScope;
  current_weather?: CurrentWeather;
}

export interface ThermalIndexRisk {
  value: number | null;
  status: string;
  category: string;
  description: string;
  reason: string | null;
  method: string;
}

export interface ThermalStressResponse {
  overall_thermal_stress: string;
  dominant_index: string;
  indices: {
    wbgt: ThermalIndexRisk;
    utci: ThermalIndexRisk;
    hi: ThermalIndexRisk;
  };
  explanation: string[];
}

export interface EstimatedHealthRisk {
  risk_level: string;
  dominant_driver: string;
  explanation: string[];
}

export interface HeatwaveOutlook {
  status: string;
  explanation: string[];
}

export interface ConsolidatedRiskResponse {
  location: {
    lat: number;
    lon: number;
  };
  timestamp: string;
  thermal_stress: ThermalStressResponse;
  estimated_health_risk: EstimatedHealthRisk;
  heatwave_outlook: HeatwaveOutlook;
}

export const getForecast = async (lat: number, lon: number, horizon_hours: number): Promise<ForecastResponse> => {
  const response = await apiClient.get<ForecastResponse>('/forecast', {
    params: {
      latitude: lat,
      longitude: lon,
      horizon_hours
    }
  });
  return response.data;
};

export const getForecastSequence = async (lat: number, lon: number): Promise<ForecastResponse[]> => {
  const response = await apiClient.get<ForecastResponse[]>('/forecast/sequence', {
    params: {
      latitude: lat,
      longitude: lon
    }
  });
  return response.data;
};

export const getUnifiedRiskForecast = async (lat: number, lon: number): Promise<ConsolidatedRiskResponse[]> => {
  const response = await apiClient.get<ConsolidatedRiskResponse[]>('/risk/forecast', {
    params: {
      lat: lat,
      lon: lon,
      days: 5
    }
  });
  return response.data;
};

// OpenStreetMap Nominatim for geocoding
export const searchLocation = async (query: string) => {
  const response = await axios.get(`https://nominatim.openstreetmap.org/search`, {
    params: {
      q: query,
      format: 'json',
      limit: 1
    }
  });
  if (response.data && response.data.length > 0) {
    return {
      lat: parseFloat(response.data[0].lat),
      lon: parseFloat(response.data[0].lon),
      display_name: response.data[0].display_name
    };
  }
  throw new Error("Location not found");
};
