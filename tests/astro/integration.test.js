"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const supertest_1 = __importDefault(require("supertest"));
const index_1 = require("../../src/index");
describe('ASTRO API Integration Tests', () => {
    describe('POST /api/v1/astro/execute', () => {
        it('should execute a tool for an agent', async () => {
            const response = await (0, supertest_1.default)(index_1.app)
                .post('/api/v1/astro/execute')
                .send({
                agentId: 'echo-agent',
                toolName: 'echo',
                input: { message: 'test' },
                userId: 'user123',
            });
            expect(response.status).toBe(200);
            expect(response.body).toMatchObject({
                requestId: expect.any(String),
                agentId: 'echo-agent',
                toolName: 'echo',
                result: {
                    ok: true,
                    data: expect.objectContaining({
                        echo: { message: 'test' },
                    }),
                    elapsedMs: expect.any(Number),
                },
            });
        });
        it('should return 400 for missing required fields', async () => {
            const response = await (0, supertest_1.default)(index_1.app).post('/api/v1/astro/execute').send({
                agentId: 'echo-agent',
                // missing toolName and input
            });
            expect(response.status).toBe(400);
            expect(response.body).toMatchObject({
                error: expect.stringContaining('Missing required fields'),
            });
        });
        it('should handle agent-tool access violations', async () => {
            const response = await (0, supertest_1.default)(index_1.app)
                .post('/api/v1/astro/execute')
                .send({
                agentId: 'math-agent', // math-agent cannot use http_request
                toolName: 'http_request',
                input: { url: 'https://jsonplaceholder.typicode.com/posts/1' },
            });
            expect(response.status).toBe(500);
            expect(response.body).toMatchObject({
                error: 'Internal Server Error',
            });
        });
        it('should execute math expressions', async () => {
            const response = await (0, supertest_1.default)(index_1.app)
                .post('/api/v1/astro/execute')
                .send({
                agentId: 'math-agent',
                toolName: 'math_eval',
                input: { expression: '5 * 4' },
            });
            expect(response.status).toBe(200);
            expect(response.body.result).toMatchObject({
                ok: true,
                data: {
                    expression: '5 * 4',
                    result: 20,
                },
            });
        });
    });
    describe('GET /api/v1/astro/agents', () => {
        it('should list all agents', async () => {
            const response = await (0, supertest_1.default)(index_1.app).get('/api/v1/astro/agents');
            expect(response.status).toBe(200);
            expect(response.body).toMatchObject({
                agents: expect.arrayContaining([
                    expect.objectContaining({
                        id: expect.any(String),
                        name: expect.any(String),
                        description: expect.any(String),
                        tools: expect.any(Array),
                    }),
                ]),
            });
            expect(response.body.agents.length).toBeGreaterThan(0);
        });
    });
    describe('GET /api/v1/astro/agents/:agentId', () => {
        it('should get details of a specific agent', async () => {
            const response = await (0, supertest_1.default)(index_1.app).get('/api/v1/astro/agents/echo-agent');
            expect(response.status).toBe(200);
            expect(response.body).toMatchObject({
                agent: {
                    id: 'echo-agent',
                    name: 'Echo Agent',
                    description: expect.any(String),
                    tools: ['echo'],
                },
            });
        });
        it('should return 404 for nonexistent agent', async () => {
            const response = await (0, supertest_1.default)(index_1.app).get('/api/v1/astro/agents/nonexistent');
            expect(response.status).toBe(404);
            expect(response.body).toMatchObject({
                error: expect.stringContaining('not found'),
            });
        });
    });
    describe('GET /api/v1/astro/tools', () => {
        it('should list all tools', async () => {
            const response = await (0, supertest_1.default)(index_1.app).get('/api/v1/astro/tools');
            expect(response.status).toBe(200);
            expect(response.body).toMatchObject({
                tools: expect.arrayContaining([
                    expect.objectContaining({
                        name: expect.any(String),
                        description: expect.any(String),
                    }),
                ]),
            });
            expect(response.body.tools.length).toBeGreaterThan(0);
        });
        it('should include echo, http_request, and math_eval tools', async () => {
            const response = await (0, supertest_1.default)(index_1.app).get('/api/v1/astro/tools');
            const toolNames = response.body.tools.map((t) => t.name);
            expect(toolNames).toContain('echo');
            expect(toolNames).toContain('http_request');
            expect(toolNames).toContain('math_eval');
        });
    });
    describe('GET /api/v1/health', () => {
        it('should return health status', async () => {
            const response = await (0, supertest_1.default)(index_1.app).get('/api/v1/health');
            expect(response.status).toBe(200);
            expect(response.body).toMatchObject({
                status: 'ok',
                timestamp: expect.any(String),
                environment: expect.any(String),
                profile: expect.any(String),
                uptime: expect.any(Number),
            });
        });
    });
    describe('GET /api/v1/version', () => {
        it('should return version information', async () => {
            const response = await (0, supertest_1.default)(index_1.app).get('/api/v1/version');
            expect(response.status).toBe(200);
            expect(response.body).toMatchObject({
                version: expect.stringContaining('1.0.0'),
                name: 'Ultimate System',
                profile: expect.any(String),
                layers: expect.objectContaining({
                    a: expect.stringContaining('IMPLEMENTED'),
                    b: expect.any(String),
                    c: expect.any(String),
                }),
            });
        });
    });
    describe('404 Handler', () => {
        it('should return 404 for unknown routes', async () => {
            const response = await (0, supertest_1.default)(index_1.app).get('/unknown/route');
            expect(response.status).toBe(404);
            expect(response.body).toMatchObject({
                error: 'Not Found',
            });
        });
    });
});
//# sourceMappingURL=integration.test.js.map