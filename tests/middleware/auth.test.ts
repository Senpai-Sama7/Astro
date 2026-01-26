import { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';
import { authenticateRequest, issueDevToken } from '../../src/middleware/auth';

// Mock logger to avoid console output
jest.mock('../../src/services/logger', () => ({
  logger: {
    warn: jest.fn(),
    info: jest.fn(),
    error: jest.fn(),
    debug: jest.fn(),
  },
}));

describe('Auth Middleware', () => {
  let mockReq: Partial<Request>;
  let mockRes: Partial<Response>;
  let mockNext: NextFunction;
  let jsonMock: jest.Mock;
  let statusMock: jest.Mock;
  const originalJwtSecret = process.env.JWT_SECRET;

  beforeEach(() => {
    // Clear JWT_SECRET to use default dev secret
    delete process.env.JWT_SECRET;
    jsonMock = jest.fn();
    statusMock = jest.fn().mockReturnValue({ json: jsonMock });
    mockReq = { headers: {}, body: {} };
    mockRes = { status: statusMock, json: jsonMock };
    mockNext = jest.fn();
  });

  afterEach(() => {
    // Restore original JWT_SECRET
    if (originalJwtSecret) {
      process.env.JWT_SECRET = originalJwtSecret;
    }
  });

  describe('authenticateRequest', () => {
    it('should reject request without token', () => {
      authenticateRequest(mockReq as Request, mockRes as Response, mockNext);

      expect(statusMock).toHaveBeenCalledWith(401);
      expect(jsonMock).toHaveBeenCalledWith({ error: 'Authorization token required' });
      expect(mockNext).not.toHaveBeenCalled();
    });

    it('should reject invalid token', () => {
      mockReq.headers = { authorization: 'Bearer invalid-token' };

      authenticateRequest(mockReq as Request, mockRes as Response, mockNext);

      expect(statusMock).toHaveBeenCalledWith(401);
      expect(jsonMock).toHaveBeenCalledWith({ error: 'Invalid or expired token' });
    });

    it('should accept valid token', () => {
      const secret = 'astro-dev-secret';
      const token = jwt.sign({ userId: 'user1', role: 'analyst' }, secret);
      mockReq.headers = { authorization: `Bearer ${token}` };

      authenticateRequest(mockReq as Request, mockRes as Response, mockNext);

      expect(mockNext).toHaveBeenCalled();
      expect((mockReq as any).user).toEqual({ userId: 'user1', role: 'analyst' });
    });

    it('should accept token with sub claim', () => {
      const secret = 'astro-dev-secret';
      const token = jwt.sign({ sub: 'user1', role: 'analyst' }, secret);
      mockReq.headers = { authorization: `Bearer ${token}` };

      authenticateRequest(mockReq as Request, mockRes as Response, mockNext);

      expect(mockNext).toHaveBeenCalled();
      expect((mockReq as any).user).toEqual({ userId: 'user1', role: 'analyst' });
    });

    it('should reject token without userId', () => {
      const secret = 'astro-dev-secret';
      const token = jwt.sign({ role: 'analyst' }, secret);
      mockReq.headers = { authorization: `Bearer ${token}` };

      authenticateRequest(mockReq as Request, mockRes as Response, mockNext);

      expect(statusMock).toHaveBeenCalledWith(401);
      expect(jsonMock).toHaveBeenCalledWith({ error: 'Token must include userId and role' });
    });

    it('should reject token without role', () => {
      const secret = 'astro-dev-secret';
      const token = jwt.sign({ userId: 'user1' }, secret);
      mockReq.headers = { authorization: `Bearer ${token}` };

      authenticateRequest(mockReq as Request, mockRes as Response, mockNext);

      expect(statusMock).toHaveBeenCalledWith(401);
      expect(jsonMock).toHaveBeenCalledWith({ error: 'Token must include userId and role' });
    });
  });

  describe('issueDevToken', () => {
    const originalEnv = process.env.NODE_ENV;

    afterEach(() => {
      process.env.NODE_ENV = originalEnv;
    });

    it('should issue token in development', () => {
      process.env.NODE_ENV = 'development';
      mockReq.body = { userId: 'user1', role: 'analyst' };

      issueDevToken(mockReq as Request, mockRes as Response);

      expect(jsonMock).toHaveBeenCalledWith(
        expect.objectContaining({
          userId: 'user1',
          role: 'analyst',
          expiresIn: '8h',
          token: expect.any(String),
        })
      );
    });

    it('should reject in production', () => {
      process.env.NODE_ENV = 'production';
      mockReq.body = { userId: 'user1', role: 'analyst' };

      issueDevToken(mockReq as Request, mockRes as Response);

      expect(statusMock).toHaveBeenCalledWith(404);
      expect(jsonMock).toHaveBeenCalledWith({ error: 'Not available' });
    });

    it('should reject missing userId', () => {
      process.env.NODE_ENV = 'development';
      mockReq.body = { role: 'analyst' };

      issueDevToken(mockReq as Request, mockRes as Response);

      expect(statusMock).toHaveBeenCalledWith(400);
      expect(jsonMock).toHaveBeenCalledWith({ error: 'Missing required fields: userId, role' });
    });

    it('should reject missing role', () => {
      process.env.NODE_ENV = 'development';
      mockReq.body = { userId: 'user1' };

      issueDevToken(mockReq as Request, mockRes as Response);

      expect(statusMock).toHaveBeenCalledWith(400);
      expect(jsonMock).toHaveBeenCalledWith({ error: 'Missing required fields: userId, role' });
    });
  });
});


describe('Auth Router', () => {
  it('should create router with dev-token endpoint', async () => {
    const { createAuthRouter } = await import('../../src/auth/router');
    const router = createAuthRouter();
    
    expect(router).toBeDefined();
    // Router has stack with routes
    expect(router.stack.length).toBeGreaterThan(0);
  });
});
