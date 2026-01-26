import { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';
import crypto from 'crypto';
import { RoleType } from '../otis/security-gateway';
import { logger } from '../services/logger';

export type AuthenticatedUser = {
  userId: string;
  role: RoleType;
};

const DEFAULT_DEV_SECRET = 'astro-dev-secret';

function getJwtSecret(): string {
  if (process.env.JWT_SECRET) {
    return process.env.JWT_SECRET;
  }
  if (process.env.NODE_ENV === 'production') {
    throw new Error('JWT_SECRET must be set in production');
  }
  logger.warn('JWT_SECRET not set; using insecure default (dev only)');
  return DEFAULT_DEV_SECRET;
}

export function authenticateRequest(req: Request, res: Response, next: NextFunction): void {
  const authHeader = req.headers.authorization;
  const token = authHeader?.startsWith('Bearer ')
    ? authHeader.substring('Bearer '.length)
    : undefined;

  let secret: string;
  try {
    secret = getJwtSecret();
  } catch (error) {
    res.status(500).json({ error: 'Server configuration error' });
    return;
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

  let secret: string;
  try {
    secret = getJwtSecret();
  } catch (error) {
    res.status(500).json({ error: 'Server configuration error' });
    return;
  }
  const token = jwt.sign({ userId, role }, secret, { expiresIn: '8h' });

  res.json({ token, userId, role, expiresIn: '8h' });
}
