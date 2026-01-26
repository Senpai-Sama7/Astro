"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const tools_1 = require("../../src/astro/tools");
const axios_1 = __importDefault(require("axios"));
jest.mock('axios');
const mockContext = {
    requestId: 'test-123',
    profile: 'core',
};
describe('Built-in Tools', () => {
    describe('echoTool', () => {
        it('should echo the input', async () => {
            const result = await (0, tools_1.echoTool)({ message: 'hello' }, mockContext);
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
            const result = await (0, tools_1.echoTool)({}, mockContext);
            expect(result.ok).toBe(true);
            expect(result.data?.echo).toEqual({});
        });
    });
    describe('httpRequestTool', () => {
        beforeEach(() => {
            jest.clearAllMocks();
        });
        it('should make a successful HTTP request', async () => {
            axios_1.default.mockResolvedValue({
                status: 200,
                statusText: 'OK',
                headers: {},
                data: { result: 'success' },
            });
            const result = await (0, tools_1.httpRequestTool)({
                url: 'https://jsonplaceholder.typicode.com/posts/1',
                method: 'GET',
            }, mockContext);
            expect(result.ok).toBe(true);
            expect(result.data?.status).toBe(200);
            expect(result.data?.data).toEqual({ result: 'success' });
        });
        it('should reject non-whitelisted domains', async () => {
            const result = await (0, tools_1.httpRequestTool)({
                url: 'https://evil.com/api',
                method: 'GET',
            }, mockContext);
            expect(result.ok).toBe(false);
            expect(result.error).toContain('not whitelisted');
        });
        it('should require url parameter', async () => {
            const result = await (0, tools_1.httpRequestTool)({}, mockContext);
            expect(result.ok).toBe(false);
            expect(result.error).toContain('url is required');
        });
        it('should reject invalid HTTP methods', async () => {
            const result = await (0, tools_1.httpRequestTool)({
                url: 'https://jsonplaceholder.typicode.com/posts/1',
                method: 'INVALID',
            }, mockContext);
            expect(result.ok).toBe(false);
            expect(result.error).toContain('not allowed');
        });
        it('should handle HTTP errors', async () => {
            axios_1.default.mockRejectedValue(new Error('Network error'));
            const result = await (0, tools_1.httpRequestTool)({
                url: 'https://jsonplaceholder.typicode.com/posts/1',
                method: 'GET',
            }, mockContext);
            expect(result.ok).toBe(false);
            expect(result.error).toContain('HTTP request failed');
        });
    });
    describe('mathEvalTool', () => {
        it('should evaluate simple arithmetic', async () => {
            const result = await (0, tools_1.mathEvalTool)({ expression: '2 + 2' }, mockContext);
            expect(result.ok).toBe(true);
            expect(result.data?.result).toBe(4);
        });
        it('should evaluate complex expressions', async () => {
            const result = await (0, tools_1.mathEvalTool)({ expression: '(10 + 5) * 2 - 3' }, mockContext);
            expect(result.ok).toBe(true);
            expect(result.data?.result).toBe(27);
        });
        it('should handle division', async () => {
            const result = await (0, tools_1.mathEvalTool)({ expression: '10 / 2' }, mockContext);
            expect(result.ok).toBe(true);
            expect(result.data?.result).toBe(5);
        });
        it('should require expression parameter', async () => {
            const result = await (0, tools_1.mathEvalTool)({}, mockContext);
            expect(result.ok).toBe(false);
            expect(result.error).toContain('expression is required');
        });
        it('should reject invalid characters', async () => {
            const result = await (0, tools_1.mathEvalTool)({ expression: '2 + 2; console.log("hack")' }, mockContext);
            expect(result.ok).toBe(false);
            expect(result.error).toContain('invalid characters');
        });
        it('should reject expressions that result in Infinity', async () => {
            const result = await (0, tools_1.mathEvalTool)({ expression: '1 / 0' }, mockContext);
            expect(result.ok).toBe(false);
            expect(result.error).toContain('infinity or NaN');
        });
        it('should reject expressions that result in NaN', async () => {
            const result = await (0, tools_1.mathEvalTool)({ expression: '0 / 0' }, mockContext);
            expect(result.ok).toBe(false);
            expect(result.error).toContain('infinity or NaN');
        });
    });
});
//# sourceMappingURL=tools.test.js.map