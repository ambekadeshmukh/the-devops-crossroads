import React, { useState, useEffect } from 'react';
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

  const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:3001';

  const fetchWeather = async (cityName: string) => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/api/weather/${cityName}`);
      setWeather(response.data);
      fetchHistory();
    } catch (error) {
      console.error('Error fetching weather:', error);
    }
    setLoading(false);
  };

  const fetchHistory = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/weather`);
      setHistory(response.data);
    } catch (error) {
      console.error('Error fetching history:', error);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

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
          {history.map((item, index) => (
            <div key={index} className="history-item">
              <strong>{item.city}</strong>: {item.temperature}°C - {item.description}
            </div>
          ))}
        </div>
      </header>
    </div>
  );
}

export default App;