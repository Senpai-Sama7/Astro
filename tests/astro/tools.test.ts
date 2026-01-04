import { echoTool, httpRequestTool, mathEvalTool } from '../../src/astro/tools';
import { ToolContext } from '../../src/astro/orchestrator';
import axios from 'axios';

jest.mock('axios');

const mockContext: ToolContext = {
  requestId: 'test-123',
  profile: 'core',
};

describe('Built-in Tools', () => {
  describe('echoTool', () => {
    it('should echo the input', async () => {
      const result = await echoTool({ message: 'hello' }, mockContext);

      expect(result.ok).toBe(true);
      expect(result.data).toEqual({
        echo: { message: 'hello' },
        context: {
          requestId: mockContext.requestId,
          profile: mockContext.profile,
        },
      });
      expect(result.elapsedMs).toBeGreaterThanOrEqual(0);
    });

    it('should handle empty input', async () => {
      const result = await echoTool({}, mockContext);

      expect(result.ok).toBe(true);
      expect(result.data?.echo).toEqual({});
    });
  });

  describe('httpRequestTool', () => {
    beforeEach(() => {
      jest.clearAllMocks();
    });

    it('should make a successful HTTP request', async () => {
      (axios as jest.Mock).mockResolvedValue({
        status: 200,
        statusText: 'OK',
        headers: {},
        data: { result: 'success' },
      });

      const result = await httpRequestTool(
        {
          url: 'https://jsonplaceholder.typicode.com/posts/1',
          method: 'GET',
        },
        mockContext
      );

      expect(result.ok).toBe(true);
      expect(result.data?.status).toBe(200);
      expect(result.data?.data).toEqual({ result: 'success' });
    });

    it('should reject non-whitelisted domains', async () => {
      const result = await httpRequestTool(
        {
          url: 'https://evil.com/api',
          method: 'GET',
        },
        mockContext
      );

      expect(result.ok).toBe(false);
      expect(result.error).toContain('not whitelisted');
    });

    it('should require url parameter', async () => {
      const result = await httpRequestTool({}, mockContext);

      expect(result.ok).toBe(false);
      expect(result.error).toContain('url is required');
    });

    it('should reject invalid HTTP methods', async () => {
      const result = await httpRequestTool(
        {
          url: 'https://jsonplaceholder.typicode.com/posts/1',
          method: 'INVALID',
        },
        mockContext
      );

      expect(result.ok).toBe(false);
      expect(result.error).toContain('not allowed');
    });

    it('should handle HTTP errors', async () => {
      (axios as jest.Mock).mockRejectedValue(new Error('Network error'));

      const result = await httpRequestTool(
        {
          url: 'https://jsonplaceholder.typicode.com/posts/1',
          method: 'GET',
        },
        mockContext
      );

      expect(result.ok).toBe(false);
      expect(result.error).toContain('HTTP request failed');
    });
  });

  describe('mathEvalTool', () => {
    it('should evaluate simple arithmetic', async () => {
      const result = await mathEvalTool({ expression: '2 + 2' }, mockContext);

      expect(result.ok).toBe(true);
      expect(result.data?.result).toBe(4);
    });

    it('should evaluate complex expressions', async () => {
      const result = await mathEvalTool(
        { expression: '(10 + 5) * 2 - 3' },
        mockContext
      );

      expect(result.ok).toBe(true);
      expect(result.data?.result).toBe(27);
    });

    it('should handle division', async () => {
      const result = await mathEvalTool({ expression: '10 / 2' }, mockContext);

      expect(result.ok).toBe(true);
      expect(result.data?.result).toBe(5);
    });

    it('should require expression parameter', async () => {
      const result = await mathEvalTool({}, mockContext);

      expect(result.ok).toBe(false);
      expect(result.error).toContain('expression is required');
    });

    it('should reject invalid characters', async () => {
      const result = await mathEvalTool(
        { expression: '2 + 2; console.log("hack")' },
        mockContext
      );

      expect(result.ok).toBe(false);
      expect(result.error).toContain('invalid characters');
    });

    it('should reject expressions that result in Infinity', async () => {
      const result = await mathEvalTool(
        { expression: '1 / 0' },
        mockContext
      );

      expect(result.ok).toBe(false);
      expect(result.error).toContain('infinity or NaN');
    });

    it('should reject expressions that result in NaN', async () => {
      const result = await mathEvalTool(
        { expression: '0 / 0' },
        mockContext
      );

      expect(result.ok).toBe(false);
      expect(result.error).toContain('infinity or NaN');
    });
  });
});
