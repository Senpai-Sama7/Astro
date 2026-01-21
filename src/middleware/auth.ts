import { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';
import { RoleType } from '../otis/security-gateway';
import { logger } from '../services/logger';

export type AuthenticatedUser = {
  userId: string;
  role: RoleType;
};

const DEFAULT_DEV_SECRET = 'astro-dev-secret';

export function authenticateRequest(req: Request, res: Response, next: NextFunction): void {
  const authHeader = req.headers.authorization;
  const token = authHeader?.startsWith('Bearer ')
    ? authHeader.substring('Bearer '.length)
    : undefined;

  const secret = process.env.JWT_SECRET || DEFAULT_DEV_SECRET;
  if (!process.env.JWT_SECRET) {
    logger.warn('JWT_SECRET is not set; using default development secret');
  }

  if (!token) {
    res.status(401).json({ error: 'Authorization token required' });
    return;
  }

  try {
    const payload = jwt.verify(token, secret) as {
      sub?: string;
      userId?: string;
      role?: RoleType;
    };

    const userId = payload.userId || payload.sub;
    const role = payload.role;

    if (!userId || !role) {
      res.status(401).json({ error: 'Token must include userId and role' });
      return;
    }

    req.user = { userId, role };
    next();
  } catch (error) {
    res.status(401).json({ error: 'Invalid or expired token' });
  }
}

export function issueDevToken(req: Request, res: Response): void {
  if (process.env.NODE_ENV === 'production') {
    res.status(404).json({ error: 'Not available' });
    return;
  }

  const { userId, role } = req.body as { userId?: string; role?: RoleType };
  if (!userId || !role) {
    res.status(400).json({ error: 'Missing required fields: userId, role' });
    return;
  }

  const secret = process.env.JWT_SECRET || DEFAULT_DEV_SECRET;
  const token = jwt.sign({ userId, role }, secret, { expiresIn: '8h' });

  res.json({ token, userId, role, expiresIn: '8h' });
}
