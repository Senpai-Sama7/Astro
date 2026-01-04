import { v4 as uuidv4 } from 'uuid';

export type ThreatLevel = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';

export interface Threat {
  id: string;
  title: string;
  description: string;
  level: ThreatLevel;
  source: string; // "ASTRO", "EXTERNAL", "OSINT", etc.
  affectedComponents: string[];
  cveIds?: string[];
  detectedAt: Date;
  updatedAt: Date;
  mitigations: string[];
  references: string[];
}

export interface ThreatIncident {
  id: string;
  threatId: string;
  status: 'OPEN' | 'INVESTIGATING' | 'MITIGATING' | 'RESOLVED';
  severity: ThreatLevel;
  createdAt: Date;
  updatedAt: Date;
  timeline: {
    timestamp: Date;
    event: string;
  }[];
  assignedTo?: string;
  notes?: string;
}

export interface C0Di3KnowledgeEntry {
  id: string;
  category: 'TACTIC' | 'TECHNIQUE' | 'PROCEDURE' | 'PATTERN' | 'INDICATOR';
  name: string;
  description: string;
  relatedThreats: string[];
  relatedTactics: string[];
  platforms: string[];
  references: string[];
  mitreTechnique?: string; // MITRE ATT&CK framework reference
}

/**
 * C0Di3: Cyber Threat Intelligence and Incident Response Layer
 * Manages threats, incidents, MITRE ATT&CK knowledge base, and threat indicators.
 */
export class C0Di3CyberIntelligence {
  private threats: Map<string, Threat> = new Map();
  private incidents: Map<string, ThreatIncident> = new Map();
  private knowledgeBase: Map<string, C0Di3KnowledgeEntry> = new Map();

  /**
   * Register a new threat in the knowledge base.
   */
  registerThreat(threat: Omit<Threat, 'id' | 'detectedAt' | 'updatedAt'>): Threat {
    if (!threat.title || !threat.level) {
      throw new Error('Threat must have title and level');
    }

    const id = uuidv4();
    const now = new Date();

    const registered: Threat = {
      ...threat,
      id,
      detectedAt: now,
      updatedAt: now,
    };

    this.threats.set(id, registered);
    return registered;
  }

  /**
   * Create an incident from a threat.
   */
  createIncident(threatId: string, severity: ThreatLevel): ThreatIncident {
    const threat = this.threats.get(threatId);
    if (!threat) {
      throw new Error(`Threat '${threatId}' not found`);
    }

    const id = uuidv4();
    const now = new Date();

    const incident: ThreatIncident = {
      id,
      threatId,
      status: 'OPEN',
      severity,
      createdAt: now,
      updatedAt: now,
      timeline: [
        {
          timestamp: now,
          event: `Incident created for threat '${threat.title}'`,
        },
      ],
    };

    this.incidents.set(id, incident);
    return incident;
  }

  /**
   * Add timeline event to an incident.
   */
  addIncidentEvent(incidentId: string, event: string): void {
    const incident = this.incidents.get(incidentId);
    if (!incident) {
      throw new Error(`Incident '${incidentId}' not found`);
    }

    incident.timeline.push({
      timestamp: new Date(),
      event,
    });
    incident.updatedAt = new Date();
  }

  /**
   * Update incident status.
   */
  updateIncidentStatus(
    incidentId: string,
    status: ThreatIncident['status']
  ): void {
    const incident = this.incidents.get(incidentId);
    if (!incident) {
      throw new Error(`Incident '${incidentId}' not found`);
    }

    incident.status = status;
    incident.updatedAt = new Date();
    this.addIncidentEvent(incidentId, `Status changed to ${status}`);
  }

  /**
   * Add knowledge base entry (MITRE ATT&CK tactic, technique, etc).
   */
  addKnowledgeEntry(
    entry: Omit<C0Di3KnowledgeEntry, 'id'>
  ): C0Di3KnowledgeEntry {
    if (!entry.name || !entry.category) {
      throw new Error('Knowledge entry must have name and category');
    }

    const id = uuidv4();
    const registered: C0Di3KnowledgeEntry = { ...entry, id };

    this.knowledgeBase.set(id, registered);
    return registered;
  }

  /**
   * Get all threats by level.
   */
  getThreatsByLevel(level: ThreatLevel): Threat[] {
    return Array.from(this.threats.values()).filter((t) => t.level === level);
  }

  /**
   * Get all critical/high threats.
   */
  getCriticalThreats(): Threat[] {
    return Array.from(this.threats.values()).filter((t) =>
      ['CRITICAL', 'HIGH'].includes(t.level)
    );
  }

  /**
   * Get open incidents.
   */
  getOpenIncidents(): ThreatIncident[] {
    return Array.from(this.incidents.values()).filter(
      (i) => i.status === 'OPEN'
    );
  }

  /**
   * Get all incidents.
   */
  getAllIncidents(): ThreatIncident[] {
    return Array.from(this.incidents.values());
  }

  /**
   * Get threat by ID.
   */
  getThreat(id: string): Threat | undefined {
    return this.threats.get(id);
  }

  /**
   * Get incident by ID.
   */
  getIncident(id: string): ThreatIncident | undefined {
    return this.incidents.get(id);
  }

  /**
   * Get knowledge entries by MITRE technique.
   */
  getKnowledgeByMitreTechnique(technique: string): C0Di3KnowledgeEntry[] {
    return Array.from(this.knowledgeBase.values()).filter(
      (e) => e.mitreTechnique === technique
    );
  }

  /**
   * Get knowledge entries by category.
   */
  getKnowledgeByCategory(
    category: C0Di3KnowledgeEntry['category']
  ): C0Di3KnowledgeEntry[] {
    return Array.from(this.knowledgeBase.values()).filter(
      (e) => e.category === category
    );
  }

  /**
   * Get threat intelligence summary.
   */
  getSummary() {
    const threats = Array.from(this.threats.values());
    const incidents = Array.from(this.incidents.values());

    return {
      totalThreats: threats.length,
      threatsBy: {
        CRITICAL: threats.filter((t) => t.level === 'CRITICAL').length,
        HIGH: threats.filter((t) => t.level === 'HIGH').length,
        MEDIUM: threats.filter((t) => t.level === 'MEDIUM').length,
        LOW: threats.filter((t) => t.level === 'LOW').length,
      },
      totalIncidents: incidents.length,
      incidentsBy: {
        OPEN: incidents.filter((i) => i.status === 'OPEN').length,
        INVESTIGATING: incidents.filter((i) => i.status === 'INVESTIGATING')
          .length,
        MITIGATING: incidents.filter((i) => i.status === 'MITIGATING').length,
        RESOLVED: incidents.filter((i) => i.status === 'RESOLVED').length,
      },
      knowledgeEntries: this.knowledgeBase.size,
    };
  }
}
