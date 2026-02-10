import { Router } from 'express';
import * as fs from 'fs';
import * as path from 'path';
import Joi from 'joi';
import { authenticateRequest } from '../middleware/auth';
import { AstroOrchestrator } from '../astro/orchestrator';
import { logger } from '../services/logger';

export interface WorkflowStep {
  id: string;
  tool: string;
  input: Record<string, unknown>;
  dependsOn?: string[];
}

export interface Workflow {
  id: string;
  name: string;
  description: string;
  steps: WorkflowStep[];
  createdAt: string;
  updatedAt: string;
}

export class WorkflowEngine {
  private workflows: Map<string, Workflow> = new Map();
  private storePath: string;

  constructor(storePath?: string) {
    this.storePath = storePath || path.join(process.cwd(), 'data', 'workflows.json');
    this.load();
  }

  private load(): void {
    if (fs.existsSync(this.storePath)) {
      const data = JSON.parse(fs.readFileSync(this.storePath, 'utf-8'));
      data.forEach((w: Workflow) => this.workflows.set(w.id, w));
    }
  }

  private save(): void {
    fs.mkdirSync(path.dirname(this.storePath), { recursive: true });
    fs.writeFileSync(this.storePath, JSON.stringify(Array.from(this.workflows.values()), null, 2));
  }

  create(workflow: Omit<Workflow, 'id' | 'createdAt' | 'updatedAt'>): Workflow {
    const id = `wf_${Date.now()}`;
    const now = new Date().toISOString();
    const w: Workflow = { ...workflow, id, createdAt: now, updatedAt: now };
    this.workflows.set(id, w);
    this.save();
    return w;
  }

  update(id: string, updates: Partial<Omit<Workflow, 'id' | 'createdAt'>>): Workflow | null {
    const w = this.workflows.get(id);
    if (!w) return null;
    Object.assign(w, updates, { updatedAt: new Date().toISOString() });
    this.save();
    return w;
  }

  delete(id: string): boolean {
    const deleted = this.workflows.delete(id);
    if (deleted) this.save();
    return deleted;
  }

  get(id: string): Workflow | undefined {
    return this.workflows.get(id);
  }

  list(): Workflow[] {
    return Array.from(this.workflows.values());
  }

  async execute(id: string, orchestrator: AstroOrchestrator, userId?: string): Promise<Record<string, unknown>> {
    const workflow = this.workflows.get(id);
    if (!workflow) throw new Error(`Workflow '${id}' not found`);

    const results: Record<string, unknown> = {};
    const completed = new Set<string>();

    const canRun = (step: WorkflowStep) => !step.dependsOn?.length || step.dependsOn.every((d) => completed.has(d));

    while (completed.size < workflow.steps.length) {
      const runnable = workflow.steps.filter((s) => !completed.has(s.id) && canRun(s));
      if (!runnable.length) throw new Error('Workflow has unresolvable dependencies');

      await Promise.all(
        runnable.map(async (step) => {
          // Resolve input references like {{stepId.field}}
          const input = JSON.parse(JSON.stringify(step.input).replace(/\{\{(\w+)\.(\w+)\}\}/g, (_, stepId, field) => {
            const r = results[stepId] as Record<string, unknown> | undefined;
            return String(r?.[field] ?? '');
          }));

          const res = await orchestrator.orchestrateToolCall({
            agentId: 'general-assistant',
            toolName: step.tool,
            input,
            userId,
          });
          results[step.id] = res.result.data;
          completed.add(step.id);
          logger.info(`Workflow ${id}: completed step ${step.id}`);
        })
      );
    }
    return results;
  }
}

const workflowStepSchema = Joi.object({
  id: Joi.string().trim().min(1).required(),
  tool: Joi.string().trim().min(1).required(),
  input: Joi.object().required(),
  dependsOn: Joi.array().items(Joi.string().trim().min(1)).optional(),
});

const workflowCreateSchema = Joi.object({
  name: Joi.string().trim().min(1).required(),
  description: Joi.string().trim().min(1).required(),
  steps: Joi.array().items(workflowStepSchema).min(1).required(),
});

const workflowUpdateSchema = Joi.object({
  name: Joi.string().trim().min(1).optional(),
  description: Joi.string().trim().min(1).optional(),
  steps: Joi.array().items(workflowStepSchema).min(1).optional(),
}).min(1);

function validateWorkflowSteps(steps: WorkflowStep[]): string | null {
  const ids = new Set<string>();
  for (const step of steps) {
    if (ids.has(step.id)) {
      return `Duplicate step id '${step.id}'`;
    }
    ids.add(step.id);
  }
  for (const step of steps) {
    const deps = step.dependsOn || [];
    for (const dep of deps) {
      if (!ids.has(dep)) {
        return `Step '${step.id}' depends on unknown step '${dep}'`;
      }
      if (dep === step.id) {
        return `Step '${step.id}' cannot depend on itself`;
      }
    }
  }
  return null;
}

export function createWorkflowRouter(engine: WorkflowEngine, orchestrator: AstroOrchestrator): Router {
  const router = Router();
  router.use(authenticateRequest);

  router.get('/', (_, res) => res.json(engine.list()));
  router.get('/:id', (req, res) => {
    const w = engine.get(req.params.id);
    w ? res.json(w) : res.status(404).json({ error: 'Not found' });
  });
  router.post('/', (req, res) => {
    const { error, value } = workflowCreateSchema.validate(req.body, { stripUnknown: true });
    if (error) {
      return res.status(400).json({ error: error.message });
    }
    const validationError = validateWorkflowSteps(value.steps as WorkflowStep[]);
    if (validationError) {
      return res.status(400).json({ error: validationError });
    }
    return res.status(201).json(engine.create(value));
  });
  router.put('/:id', (req, res) => {
    const { error, value } = workflowUpdateSchema.validate(req.body, { stripUnknown: true });
    if (error) {
      return res.status(400).json({ error: error.message });
    }
    if (value.steps) {
      const validationError = validateWorkflowSteps(value.steps as WorkflowStep[]);
      if (validationError) {
        return res.status(400).json({ error: validationError });
      }
    }
    const w = engine.update(req.params.id, value);
    w ? res.json(w) : res.status(404).json({ error: 'Not found' });
  });
  router.delete('/:id', (req, res) => {
    engine.delete(req.params.id) ? res.status(204).send() : res.status(404).json({ error: 'Not found' });
  });
  router.post('/:id/execute', async (req, res) => {
    try {
      const results = await engine.execute(req.params.id, orchestrator, req.user?.userId);
      res.json({ success: true, results });
    } catch (e) {
      res.status(400).json({ error: String(e) });
    }
  });

  return router;
}
