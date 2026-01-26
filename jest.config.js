module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/src', '<rootDir>/tests'],
  testMatch: ['**/__tests__/**/*.ts', '**/?(*.)+(spec|test).ts'],
  moduleFileExtensions: ['ts', 'js', 'json'],
  collectCoverageFrom: [
    'src/**/*.ts',
    '!src/**/*.d.ts',
    '!src/index.ts',
    '!src/**/index.ts',
    '!src/**/router.ts',  // Exclude Express routers (boilerplate)
    '!src/services/websocket.ts',  // WebSocket server (integration tested)
    '!src/services/llm.ts',  // LLM providers (requires API keys)
    '!src/services/metrics.ts',  // Metrics (simple collector)
    '!src/plugins/**',  // Plugin system (integration tested)
    '!src/workflows/**',  // Workflow engine (integration tested)
  ],
  coverageThreshold: {
    global: {
      branches: 55,
      functions: 75,
      lines: 75,
      statements: 75,
    },
  },
  setupFilesAfterEnv: ['<rootDir>/tests/setup.ts'],
  testTimeout: 30000,
  globals: {
    'ts-jest': {
      tsconfig: {
        esModuleInterop: true,
      },
    },
  },
};
