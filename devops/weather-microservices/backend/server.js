const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const axios = require('axios');
require('dotenv').config();
const promClient = require('prom-client');


const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json());

// MongoDB Connection
mongoose.connect(process.env.MONGODB_URI || 'mongodb://mongodb:27017/weather', {
  useNewUrlParser: true,
  useUnifiedTopology: true,
});

// Weather Schema
const weatherSchema = new mongoose.Schema({
  city: String,
  temperature: Number,
  description: String,
  timestamp: { type: Date, default: Date.now }
});

const Weather = mongoose.model('Weather', weatherSchema);

// Routes
app.get('/health', (req, res) => {
  res.json({ status: 'OK', service: 'weather-backend' });
});

app.get('/api/weather/:city', async (req, res) => {
  try {
    const { city } = req.params;
    
    // Mock weather data (replace with real API)
    const weatherData = {
      city,
      temperature: Math.floor(Math.random() * 30) + 10,
      description: ['Sunny', 'Cloudy', 'Rainy', 'Snowy'][Math.floor(Math.random() * 4)],
    };

    // Save to database
    const weather = new Weather(weatherData);
    await weather.save();

    res.json(weatherData);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.get('/api/weather', async (req, res) => {
  try {
    const weather = await Weather.find().sort({ timestamp: -1 }).limit(10);
    res.json(weather);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.listen(PORT, () => {
  console.log(`Backend service running on port ${PORT}`);
});
// Create metrics
const httpDuration = new promClient.Histogram({
    name: 'http_request_duration_seconds',
    help: 'Duration of HTTP requests in seconds',
    labelNames: ['method', 'route', 'status_code']
  });
  
  const httpRequests = new promClient.Counter({
    name: 'http_requests_total',
    help: 'Total number of HTTP requests',
    labelNames: ['method', 'route', 'status_code']
  });
  
  // Middleware for metrics
  app.use((req, res, next) => {
    const start = Date.now();
    
    res.on('finish', () => {
      const duration = (Date.now() - start) / 1000;
      const route = req.route ? req.route.path : req.path;
      
      httpDuration
        .labels(req.method, route, res.statusCode.toString())
        .observe(duration);
      
      httpRequests
        .labels(req.method, route, res.statusCode.toString())
        .inc();
    });
    
    next();
  });
  
  // Metrics endpoint
  app.get('/metrics', (req, res) => {
    res.set('Content-Type', promClient.register.contentType);
    res.end(promClient.register.metrics());
  });

module.exports = app;