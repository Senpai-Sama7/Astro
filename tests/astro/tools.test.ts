import {
  echoTool,
  httpRequestTool,
  mathEvalTool,
  webSearchTool,
  contentExtractTool,
  readFileTool,
  writeFileTool,
  listDirTool,
  gitStatusTool,
  gitDiffTool,
  runTestsTool,
  lintCodeTool,
  saveKnowledgeTool,
  retrieveKnowledgeTool,
} from '../../src/astro/tools';
import { ToolContext } from '../../src/astro/orchestrator';
import axios from 'axios';
import * as fs from 'fs';
import * as childProcess from 'child_process';
import * as path from 'path';

jest.mock('axios');
jest.mock('fs');
jest.mock('child_process');

const mockContext: ToolContext = {
  requestId: 'test-123',
  profile: 'core',
};

describe('Built-in Tools', () => {
  beforeEach(() => jest.clearAllMocks());

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
      expect(result.data).toBeDefined();
    });

    it('should reject invalid URLs', async () => {
      const result = await httpRequestTool(
        { url: 'not-a-valid-url', method: 'GET' },
        mockContext
      );
      expect(result.ok).toBe(false);
      expect(result.error).toContain('not whitelisted');
    });
  });

  describe('httpRequestTool', () => {
    beforeEach(() => {
      jest.clearAllMocks();
    });

    it('should make a successful HTTP request', async () => {
      (axios as unknown as jest.Mock).mockResolvedValue({
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
      expect((result.data as any)?.status).toBe(200);
      expect((result.data as any)?.data).toEqual({ result: 'success' });
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
      (axios as unknown as jest.Mock).mockRejectedValue(new Error('Network error'));

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
      expect((result.data as any)?.result).toBe(4);
    });

    it('should evaluate complex expressions', async () => {
      const result = await mathEvalTool(
        { expression: '(10 + 5) * 2 - 3' },
        mockContext
      );

      expect(result.ok).toBe(true);
      expect((result.data as any)?.result).toBe(27);
    });

    it('should handle division', async () => {
      const result = await mathEvalTool({ expression: '10 / 2' }, mockContext);

      expect(result.ok).toBe(true);
      expect((result.data as any)?.result).toBe(5);
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

    it('should handle syntax errors in expressions', async () => {
      const result = await mathEvalTool(
        { expression: '((2 + 3' },
        mockContext
      );

      expect(result.ok).toBe(false);
      expect(result.error).toContain('Math evaluation failed');
    });
  });
});


describe('Research Agent Tools', () => {
  beforeEach(() => jest.clearAllMocks());

  describe('webSearchTool', () => {
    it('should search and return results', async () => {
      (axios.get as jest.Mock).mockResolvedValue({
        data: '<a class="result__a" href="http://example.com">Example</a>',
      });
      const result = await webSearchTool({ query: 'test' }, mockContext);
      expect(result.ok).toBe(true);
      expect((result.data as any).query).toBe('test');
    });

    it('should require query parameter', async () => {
      const result = await webSearchTool({}, mockContext);
      expect(result.ok).toBe(false);
      expect(result.error).toContain('query is required');
    });

    it('should handle search errors', async () => {
      (axios.get as jest.Mock).mockRejectedValue(new Error('Network error'));
      const result = await webSearchTool({ query: 'test' }, mockContext);
      expect(result.ok).toBe(false);
      expect(result.error).toContain('Web search failed');
    });
  });

  describe('contentExtractTool', () => {
    it('should extract content from URL', async () => {
      (axios.get as jest.Mock).mockResolvedValue({ data: '<html><body>Hello World</body></html>' });
      const result = await contentExtractTool({ url: 'http://example.com' }, mockContext);
      expect(result.ok).toBe(true);
      expect((result.data as any).content).toContain('Hello World');
    });

    it('should require url parameter', async () => {
      const result = await contentExtractTool({}, mockContext);
      expect(result.ok).toBe(false);
      expect(result.error).toContain('url is required');
    });

    it('should handle extraction errors', async () => {
      (axios.get as jest.Mock).mockRejectedValue(new Error('Timeout'));
      const result = await contentExtractTool({ url: 'http://example.com' }, mockContext);
      expect(result.ok).toBe(false);
      expect(result.error).toContain('Content extraction failed');
    });
  });
});

describe('FileSystem Agent Tools', () => {
  beforeEach(() => jest.clearAllMocks());

  describe('readFileTool', () => {
    it('should read file content', async () => {
      (fs.readFileSync as jest.Mock).mockReturnValue('file content');
      const result = await readFileTool({ path: 'test.txt' }, mockContext);
      expect(result.ok).toBe(true);
      expect((result.data as any).content).toBe('file content');
    });

    it('should require path parameter', async () => {
      const result = await readFileTool({}, mockContext);
      expect(result.ok).toBe(false);
      expect(result.error).toContain('path is required');
    });

    it('should reject paths outside workspace', async () => {
      const result = await readFileTool({ path: '../../../etc/passwd' }, mockContext);
      expect(result.ok).toBe(false);
      expect(result.error).toContain('outside workspace');
    });

    it('should handle read errors', async () => {
      (fs.readFileSync as jest.Mock).mockImplementation(() => { throw new Error('ENOENT'); });
      const result = await readFileTool({ path: 'missing.txt' }, mockContext);
      expect(result.ok).toBe(false);
      expect(result.error).toContain('Read file failed');
    });
  });

  describe('writeFileTool', () => {
    it('should write file content', async () => {
      (fs.mkdirSync as jest.Mock).mockReturnValue(undefined);
      (fs.writeFileSync as jest.Mock).mockReturnValue(undefined);
      const result = await writeFileTool({ path: 'test.txt', content: 'hello' }, mockContext);
      expect(result.ok).toBe(true);
      expect((result.data as any).written).toBe(5);
    });

    it('should require path and content', async () => {
      const result = await writeFileTool({ path: 'test.txt' }, mockContext);
      expect(result.ok).toBe(false);
      expect(result.error).toContain('path and content are required');
    });

    it('should reject paths outside workspace', async () => {
      const result = await writeFileTool({ path: '../../../tmp/hack', content: 'x' }, mockContext);
      expect(result.ok).toBe(false);
      expect(result.error).toContain('outside workspace');
    });

    it('should handle write errors', async () => {
      (fs.mkdirSync as jest.Mock).mockImplementation(() => { throw new Error('EACCES'); });
      const result = await writeFileTool({ path: 'test.txt', content: 'x' }, mockContext);
      expect(result.ok).toBe(false);
      expect(result.error).toContain('Write file failed');
    });
  });

  describe('listDirTool', () => {
    it('should list directory contents', async () => {
      (fs.readdirSync as jest.Mock).mockReturnValue([
        { name: 'file.txt', isDirectory: () => false },
        { name: 'subdir', isDirectory: () => true },
      ]);
      const result = await listDirTool({ path: '.' }, mockContext);
      expect(result.ok).toBe(true);
      expect((result.data as any).entries).toHaveLength(2);
    });

    it('should reject paths outside workspace', async () => {
      const result = await listDirTool({ path: '../../../' }, mockContext);
      expect(result.ok).toBe(false);
      expect(result.error).toContain('outside workspace');
    });

    it('should handle list errors', async () => {
      (fs.readdirSync as jest.Mock).mockImplementation(() => { throw new Error('ENOENT'); });
      const result = await listDirTool({ path: 'missing' }, mockContext);
      expect(result.ok).toBe(false);
      expect(result.error).toContain('List dir failed');
    });
  });
});

describe('Git Agent Tools', () => {
  beforeEach(() => jest.clearAllMocks());

  describe('gitStatusTool', () => {
    it('should return git status', async () => {
      (childProcess.execSync as jest.Mock)
        .mockReturnValueOnce('M file.txt\n')
        .mockReturnValueOnce('main\n');
      const result = await gitStatusTool({}, mockContext);
      expect(result.ok).toBe(true);
      expect((result.data as any).branch).toBe('main');
      expect((result.data as any).status).toContain('M file.txt');
    });

    it('should handle git errors', async () => {
      (childProcess.execSync as jest.Mock).mockImplementation(() => { throw new Error('not a git repo'); });
      const result = await gitStatusTool({}, mockContext);
      expect(result.ok).toBe(false);
      expect(result.error).toContain('Git status failed');
    });
  });

  describe('gitDiffTool', () => {
    it('should return git diff', async () => {
      (childProcess.execSync as jest.Mock).mockReturnValue('diff --git a/file.txt');
      const result = await gitDiffTool({}, mockContext);
      expect(result.ok).toBe(true);
      expect((result.data as any).diff).toContain('diff --git');
    });

    it('should diff specific file', async () => {
      (childProcess.execSync as jest.Mock).mockReturnValue('diff for file');
      const result = await gitDiffTool({ file: 'test.txt' }, mockContext);
      expect(result.ok).toBe(true);
    });

    it('should handle diff errors', async () => {
      (childProcess.execSync as jest.Mock).mockImplementation(() => { throw new Error('error'); });
      const result = await gitDiffTool({}, mockContext);
      expect(result.ok).toBe(false);
      expect(result.error).toContain('Git diff failed');
    });
  });
});

describe('Test Agent Tools', () => {
  beforeEach(() => jest.clearAllMocks());

  describe('runTestsTool', () => {
    it('should run tests with provided command', async () => {
      (childProcess.execSync as jest.Mock).mockReturnValue('All tests passed');
      const result = await runTestsTool({ command: 'npm test' }, mockContext);
      expect(result.ok).toBe(true);
      expect((result.data as any).output).toContain('passed');
    });

    it('should auto-detect npm test', async () => {
      (fs.existsSync as jest.Mock).mockReturnValue(true);
      (childProcess.execSync as jest.Mock).mockReturnValue('Tests passed');
      const result = await runTestsTool({}, mockContext);
      expect(result.ok).toBe(true);
    });

    it('should auto-detect pytest', async () => {
      (fs.existsSync as jest.Mock).mockImplementation((p: string) => p.includes('pytest.ini'));
      (childProcess.execSync as jest.Mock).mockReturnValue('pytest passed');
      const result = await runTestsTool({}, mockContext);
      expect(result.ok).toBe(true);
    });

    it('should fail if no test framework detected', async () => {
      (fs.existsSync as jest.Mock).mockReturnValue(false);
      const result = await runTestsTool({}, mockContext);
      expect(result.ok).toBe(false);
      expect(result.error).toContain('Could not detect');
    });

    it('should handle test failures', async () => {
      (fs.existsSync as jest.Mock).mockReturnValue(true);
      (childProcess.execSync as jest.Mock).mockImplementation(() => {
        const err: any = new Error('Tests failed');
        err.stdout = 'FAIL test.ts';
        throw err;
      });
      const result = await runTestsTool({}, mockContext);
      expect(result.ok).toBe(false);
      expect(result.error).toContain('Tests failed');
    });
  });
});

describe('Analysis Agent Tools', () => {
  beforeEach(() => jest.clearAllMocks());

  describe('lintCodeTool', () => {
    it('should run eslint when package.json exists', async () => {
      (fs.existsSync as jest.Mock).mockReturnValue(true);
      (childProcess.execSync as jest.Mock).mockReturnValue('[]');
      const result = await lintCodeTool({}, mockContext);
      expect(result.ok).toBe(true);
    });

    it('should run specified linter', async () => {
      (childProcess.execSync as jest.Mock).mockReturnValue('[]');
      const result = await lintCodeTool({ linter: 'eslint', path: 'src' }, mockContext);
      expect(result.ok).toBe(true);
    });

    it('should run pylint when specified', async () => {
      (childProcess.execSync as jest.Mock).mockReturnValue('[]');
      const result = await lintCodeTool({ linter: 'pylint' }, mockContext);
      expect(result.ok).toBe(true);
    });

    it('should auto-detect pylint for Python projects', async () => {
      (fs.existsSync as jest.Mock).mockImplementation((p: string) => p === 'pyproject.toml');
      (childProcess.execSync as jest.Mock).mockReturnValue('[]');
      const result = await lintCodeTool({}, mockContext);
      expect(result.ok).toBe(true);
    });

    it('should fail if no linter detected', async () => {
      (fs.existsSync as jest.Mock).mockReturnValue(false);
      const result = await lintCodeTool({}, mockContext);
      expect(result.ok).toBe(false);
      expect(result.error).toContain('No linter detected');
    });

    it('should handle lint issues gracefully', async () => {
      (fs.existsSync as jest.Mock).mockReturnValue(true);
      (childProcess.execSync as jest.Mock).mockImplementation(() => {
        const err: any = new Error('Lint issues');
        err.stdout = '[{"severity": 2}]';
        throw err;
      });
      const result = await lintCodeTool({}, mockContext);
      expect(result.ok).toBe(true); // Lint issues are not failures
    });
  });
});

describe('Knowledge Agent Tools', () => {
  beforeEach(() => jest.clearAllMocks());

  describe('saveKnowledgeTool', () => {
    it('should save knowledge', async () => {
      (fs.existsSync as jest.Mock).mockReturnValue(false);
      (fs.mkdirSync as jest.Mock).mockReturnValue(undefined);
      (fs.writeFileSync as jest.Mock).mockReturnValue(undefined);
      const result = await saveKnowledgeTool({ key: 'test', value: 'data' }, mockContext);
      expect(result.ok).toBe(true);
      expect((result.data as any).saved).toBe(true);
    });

    it('should require key parameter', async () => {
      const result = await saveKnowledgeTool({ value: 'data' }, mockContext);
      expect(result.ok).toBe(false);
      expect(result.error).toContain('key is required');
    });

    it('should append to existing knowledge', async () => {
      (fs.existsSync as jest.Mock).mockReturnValue(true);
      (fs.readFileSync as jest.Mock).mockReturnValue('{"existing": {"value": 1}}');
      (fs.mkdirSync as jest.Mock).mockReturnValue(undefined);
      (fs.writeFileSync as jest.Mock).mockReturnValue(undefined);
      const result = await saveKnowledgeTool({ key: 'new', value: 'data' }, mockContext);
      expect(result.ok).toBe(true);
    });

    it('should handle save errors', async () => {
      (fs.existsSync as jest.Mock).mockReturnValue(false);
      (fs.mkdirSync as jest.Mock).mockImplementation(() => { throw new Error('EACCES'); });
      const result = await saveKnowledgeTool({ key: 'test', value: 'x' }, mockContext);
      expect(result.ok).toBe(false);
      expect(result.error).toContain('Save knowledge failed');
    });
  });

  describe('retrieveKnowledgeTool', () => {
    it('should retrieve all keys when no key specified', async () => {
      (fs.existsSync as jest.Mock).mockReturnValue(true);
      (fs.readFileSync as jest.Mock).mockReturnValue('{"a": {"value": 1}, "b": {"value": 2}}');
      const result = await retrieveKnowledgeTool({}, mockContext);
      expect(result.ok).toBe(true);
      expect((result.data as any).keys).toEqual(['a', 'b']);
    });

    it('should retrieve specific key', async () => {
      (fs.existsSync as jest.Mock).mockReturnValue(true);
      (fs.readFileSync as jest.Mock).mockReturnValue('{"test": {"value": "data"}}');
      const result = await retrieveKnowledgeTool({ key: 'test' }, mockContext);
      expect(result.ok).toBe(true);
      expect((result.data as any).value).toEqual({ value: 'data' });
    });

    it('should return null for missing key', async () => {
      (fs.existsSync as jest.Mock).mockReturnValue(true);
      (fs.readFileSync as jest.Mock).mockReturnValue('{}');
      const result = await retrieveKnowledgeTool({ key: 'missing' }, mockContext);
      expect(result.ok).toBe(true);
      expect((result.data as any).value).toBeNull();
    });

    it('should return empty when no knowledge file', async () => {
      (fs.existsSync as jest.Mock).mockReturnValue(false);
      const result = await retrieveKnowledgeTool({}, mockContext);
      expect(result.ok).toBe(true);
      expect((result.data as any).knowledge).toEqual({});
    });

    it('should handle retrieve errors', async () => {
      (fs.existsSync as jest.Mock).mockReturnValue(true);
      (fs.readFileSync as jest.Mock).mockImplementation(() => { throw new Error('EACCES'); });
      const result = await retrieveKnowledgeTool({}, mockContext);
      expect(result.ok).toBe(false);
      expect(result.error).toContain('Retrieve knowledge failed');
    });
  });
});


describe('Utility Tools', () => {
  beforeEach(() => jest.clearAllMocks());

  describe('jsonQueryTool', () => {
    it('should query JSON with dot notation', async () => {
      const { jsonQueryTool } = await import('../../src/astro/tools');
      const result = await jsonQueryTool({ data: { a: { b: 1 } }, query: 'a.b' }, mockContext);
      expect(result.ok).toBe(true);
      expect((result.data as any).result).toBe(1);
    });

    it('should require data and query', async () => {
      const { jsonQueryTool } = await import('../../src/astro/tools');
      const result = await jsonQueryTool({}, mockContext);
      expect(result.ok).toBe(false);
    });
  });

  describe('textTransformTool', () => {
    it('should transform text to uppercase', async () => {
      const { textTransformTool } = await import('../../src/astro/tools');
      const result = await textTransformTool({ text: 'hello', operation: 'upper' }, mockContext);
      expect(result.ok).toBe(true);
      expect((result.data as any).result).toBe('HELLO');
    });

    it('should encode base64', async () => {
      const { textTransformTool } = await import('../../src/astro/tools');
      const result = await textTransformTool({ text: 'hello', operation: 'base64_encode' }, mockContext);
      expect(result.ok).toBe(true);
      expect((result.data as any).result).toBe('aGVsbG8=');
    });

    it('should reject unknown operation', async () => {
      const { textTransformTool } = await import('../../src/astro/tools');
      const result = await textTransformTool({ text: 'hello', operation: 'unknown' }, mockContext);
      expect(result.ok).toBe(false);
    });
  });

  describe('timestampTool', () => {
    it('should return current timestamp', async () => {
      const { timestampTool } = await import('../../src/astro/tools');
      const result = await timestampTool({ operation: 'now' }, mockContext);
      expect(result.ok).toBe(true);
      expect((result.data as any).iso).toBeDefined();
    });

    it('should parse timestamp', async () => {
      const { timestampTool } = await import('../../src/astro/tools');
      const result = await timestampTool({ operation: 'parse', value: '2024-01-01' }, mockContext);
      expect(result.ok).toBe(true);
      expect((result.data as any).valid).toBe(true);
    });
  });

  describe('hashTool', () => {
    it('should compute sha256 hash', async () => {
      const { hashTool } = await import('../../src/astro/tools');
      const result = await hashTool({ text: 'hello' }, mockContext);
      expect(result.ok).toBe(true);
      expect((result.data as any).algorithm).toBe('sha256');
      expect((result.data as any).hash).toHaveLength(64);
    });

    it('should require text', async () => {
      const { hashTool } = await import('../../src/astro/tools');
      const result = await hashTool({}, mockContext);
      expect(result.ok).toBe(false);
    });
  });

  describe('uuidTool', () => {
    it('should generate UUID', async () => {
      const { uuidTool } = await import('../../src/astro/tools');
      const result = await uuidTool({}, mockContext);
      expect(result.ok).toBe(true);
      expect((result.data as any).uuids).toHaveLength(1);
    });

    it('should generate multiple UUIDs', async () => {
      const { uuidTool } = await import('../../src/astro/tools');
      const result = await uuidTool({ count: 3 }, mockContext);
      expect(result.ok).toBe(true);
      expect((result.data as any).uuids).toHaveLength(3);
    });
  });

  describe('systemInfoTool', () => {
    it('should return OS info', async () => {
      const { systemInfoTool } = await import('../../src/astro/tools');
      const result = await systemInfoTool({ type: 'os' }, mockContext);
      expect(result.ok).toBe(true);
      expect((result.data as any).platform).toBeDefined();
    });

    it('should return memory info', async () => {
      const { systemInfoTool } = await import('../../src/astro/tools');
      const result = await systemInfoTool({ type: 'memory' }, mockContext);
      expect(result.ok).toBe(true);
      expect((result.data as any).heapUsed).toBeDefined();
    });
  });
});
