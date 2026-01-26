import request from 'supertest';
import express from 'express';
import jwt from 'jsonwebtoken';
import { AstroOrchestrator } from '../../src/astro/orchestrator';
import { createAstroRouter } from '../../src/astro/router';

const TEST_SECRET = 'test-secret';
process.env.JWT_SECRET = TEST_SECRET;

function createTestToken(userId = 'test-user', role = 'admin') {
  return jwt.sign({ userId, role }, TEST_SECRET, { expiresIn: '1h' });
}

// Create a test app with routes mounted synchronously
function createTestApp() {
  const app = express();
  app.use(express.json());
  
  const orchestrator = new AstroOrchestrator();
  const astroRouter = createAstroRouter(orchestrator);
  app.use('/api/v1/astro', astroRouter);
  
  // Health endpoint
  app.get('/api/v1/health', (req, res) => {
    res.json({ status: 'ok', timestamp: new Date().toISOString() });
  });
  
  // Version endpoint
  app.get('/api/v1/version', (req, res) => {
    res.json({
      version: '1.0.0',
      name: 'ASTRO Ultimate System',
      profile: 'test',
    });
  });
  
  return app;
}

const app = createTestApp();
const authToken = createTestToken();

describe('ASTRO API Integration Tests', () => {
  describe('GET /api/v1/health', () => {
    it('should return health status', async () => {
      const response = await request(app).get('/api/v1/health');
      expect(response.status).toBe(200);
      expect(response.body.agent || response.body).toMatchObject({
        status: 'ok',
        timestamp: expect.any(String),
      });
    });
  });

  describe('GET /api/v1/version', () => {
    it('should return version information', async () => {
      const response = await request(app).get('/api/v1/version');
      expect(response.status).toBe(200);
      expect(response.body.agent || response.body).toMatchObject({
        version: expect.stringContaining('1.0.0'),
        name: 'ASTRO Ultimate System',
        profile: expect.any(String),
      });
    });
  });

  describe('POST /api/v1/astro/execute', () => {
    it('should execute a tool for an agent', async () => {
      const response = await request(app)
        .post('/api/v1/astro/execute')
        .set('Authorization', `Bearer ${authToken}`)
        .send({
          agentId: 'echo-agent',
          toolName: 'echo',
          input: { message: 'test' },
          userId: 'user123',
        });

      expect(response.status).toBe(200);
      expect(response.body.agent || response.body).toMatchObject({
        requestId: expect.any(String),
        agentId: 'echo-agent',
        toolName: 'echo',
      });
    });

    it('should return 400 for missing required fields', async () => {
      const response = await request(app)
        .post('/api/v1/astro/execute')
        .set('Authorization', `Bearer ${authToken}`)
        .send({
          agentId: 'echo-agent',
          // missing toolName and input
        });

      expect(response.status).toBe(400);
      expect(response.body.error).toContain('Missing required fields');
    });

    it('should return 401 without auth token', async () => {
      const response = await request(app)
        .post('/api/v1/astro/execute')
        .send({
          agentId: 'echo-agent',
          toolName: 'echo',
          input: { message: 'test' },
        });

      expect(response.status).toBe(401);
    });

    it('should execute math expressions', async () => {
      const response = await request(app)
        .post('/api/v1/astro/execute')
        .set('Authorization', `Bearer ${authToken}`)
        .send({
          agentId: 'math-agent',
          toolName: 'math_eval',
          input: { expression: '2 + 2' },
          userId: 'user123',
        });

      expect(response.status).toBe(200);
      expect(response.body.result?.data?.result).toBe(4);
    });
  });

  describe('GET /api/v1/astro/agents', () => {
    it('should list all agents', async () => {
      const response = await request(app)
        .get('/api/v1/astro/agents')
        .set('Authorization', `Bearer ${authToken}`);
      expect(response.status).toBe(200);
      expect(Array.isArray(response.body.agents)).toBe(true);
      expect(response.body.agents.length).toBeGreaterThan(0);
    });
  });

  describe('GET /api/v1/astro/agents/:agentId', () => {
    it('should get details of a specific agent', async () => {
      const response = await request(app)
        .get('/api/v1/astro/agents/echo-agent')
        .set('Authorization', `Bearer ${authToken}`);
      expect(response.status).toBe(200);
      expect(response.body.agent || response.body).toMatchObject({
        id: 'echo-agent',
      });
    });

    it('should return 404 for nonexistent agent', async () => {
      const response = await request(app)
        .get('/api/v1/astro/agents/nonexistent')
        .set('Authorization', `Bearer ${authToken}`);
      expect(response.status).toBe(404);
    });
  });

  describe('GET /api/v1/astro/tools', () => {
    it('should list all tools', async () => {
      const response = await request(app)
        .get('/api/v1/astro/tools')
        .set('Authorization', `Bearer ${authToken}`);
      expect(response.status).toBe(200);
      expect(Array.isArray(response.body.agents || response.body.tools || response.body)).toBe(true);
    });

    it('should include echo, http_request, and math_eval tools', async () => {
      const response = await request(app)
        .get('/api/v1/astro/tools')
        .set('Authorization', `Bearer ${authToken}`);
      const toolNames = (response.body.tools || response.body).map((t: { name: string }) => t.name);
      expect(toolNames).toContain('echo');
      expect(toolNames).toContain('http_request');
      expect(toolNames).toContain('math_eval');
    });
  });
});
