import { Router, Request, Response } from 'express';
import { issueDevToken } from '../middleware/auth';

export function createAuthRouter(): Router {
  const router = Router();

  router.post('/dev-token', (req: Request, res: Response) => {
    issueDevToken(req, res);
  });

  return router;
}
