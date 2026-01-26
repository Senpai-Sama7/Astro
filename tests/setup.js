"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
// Jest setup file
const dotenv_1 = __importDefault(require("dotenv"));
// Load test environment variables
dotenv_1.default.config({ path: '.env.test' });
// Set test environment
process.env.NODE_ENV = 'test';
process.env.LOG_LEVEL = 'error';
// Suppress console logs during tests
global.console = {
    ...console,
    log: jest.fn(),
    debug: jest.fn(),
    info: jest.fn(),
    warn: jest.fn(),
    // Keep error for debugging
};
// Default timeout for tests
jest.setTimeout(30000);
//# sourceMappingURL=setup.js.map