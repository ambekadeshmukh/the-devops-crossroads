const request = require('supertest');
const app = require('../server');

describe('Weather API', () => {
  test('Health check endpoint', async () => {
    const response = await request(app).get('/health');
    expect(response.status).toBe(200);
    expect(response.body.status).toBe('OK');
  });

  test('Get weather for city', async () => {
    const response = await request(app).get('/api/weather/London');
    expect(response.status).toBe(200);
    expect(response.body.city).toBe('London');
  });
});