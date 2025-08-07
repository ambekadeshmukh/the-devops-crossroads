import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import './App.css';

interface WeatherData {
  _id?: string;
  city: string;
  temperature: number;
  description: string;
  timestamp?: string;
}

function App() {
  const [city, setCity] = useState('');
  const [weather, setWeather] = useState<WeatherData | null>(null);
  const [history, setHistory] = useState<WeatherData[]>([]);
  const [loading, setLoading] = useState(false);

  const API_BASE = process.env.REACT_APP_API_URL || '';

  // Fetch latest weather for a city
  const fetchHistory = useCallback(async () => {
    try {
      const response = await axios.get<WeatherData[]>(`${API_BASE}/api/weather`);
      setHistory(response.data);
    } catch (error) {
      console.error('Error fetching history:', error);
    }
  }, [API_BASE]);

  const fetchWeather = useCallback(async (cityName: string) => {
    setLoading(true);
    try {
      const response = await axios.get<WeatherData>(`${API_BASE}/api/weather/${cityName}`);
      setWeather(response.data);
      await fetchHistory();
    } catch (error) {
      console.error('Error fetching weather:', error);
    } finally {
      setLoading(false);
    }
  }, [API_BASE, fetchHistory]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (city.trim()) {
      fetchWeather(city.trim());
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Weather Microservices App</h1>
        
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            value={city}
            onChange={(e) => setCity(e.target.value)}
            placeholder="Enter city name"
            disabled={loading}
          />
          <button type="submit" disabled={loading}>
            {loading ? 'Loading...' : 'Get Weather'}
          </button>
        </form>

        {weather && (
          <div className="weather-result">
            <h2>{weather.city}</h2>
            <p>Temperature: {weather.temperature}°C</p>
            <p>Description: {weather.description}</p>
          </div>
        )}

        <div className="weather-history">
          <h3>Recent Searches</h3>
          {history.map((item) => (
            <div key={item._id ?? `${item.city}-${item.timestamp}`} className="history-item">
              <strong>{item.city}</strong>: {item.temperature}°C - {item.description}
            </div>
          ))}
        </div>
      </header>
    </div>
  );
}

export default App;