"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const threat_intelligence_1 = require("../../src/codi3/threat-intelligence");
describe('C0Di3 Cyber Threat Intelligence', () => {
    let c0di3;
    beforeEach(() => {
        c0di3 = new threat_intelligence_1.C0Di3CyberIntelligence();
    });
    describe('Threat Registration', () => {
        it('should register a new threat', () => {
            const threat = c0di3.registerThreat({
                title: 'SQL Injection Vulnerability',
                description: 'XSS vulnerability in user input',
                level: 'HIGH',
                source: 'ASTRO',
                affectedComponents: ['api', 'web'],
                cveIds: ['CVE-2024-1234'],
                mitigations: ['Input validation', 'Parameterized queries'],
                references: ['https://example.com/advisory'],
            });
            expect(threat.id).toBeDefined();
            expect(threat.title).toBe('SQL Injection Vulnerability');
            expect(threat.level).toBe('HIGH');
            expect(threat.detectedAt).toBeDefined();
        });
        it('should require title and level', () => {
            expect(() => {
                c0di3.registerThreat({
                    title: '',
                    description: 'Test',
                    level: 'HIGH',
                    source: 'TEST',
                    affectedComponents: [],
                    mitigations: [],
                    references: [],
                });
            }).toThrow();
        });
        it('should retrieve threat by ID', () => {
            const registered = c0di3.registerThreat({
                title: 'Test Threat',
                description: 'A test threat',
                level: 'MEDIUM',
                source: 'TEST',
                affectedComponents: [],
                mitigations: [],
                references: [],
            });
            const retrieved = c0di3.getThreat(registered.id);
            expect(retrieved).toBeDefined();
            expect(retrieved?.title).toBe('Test Threat');
        });
    });
    describe('Threat Queries', () => {
        beforeEach(() => {
            c0di3.registerThreat({
                title: 'Critical Threat',
                description: 'A critical threat',
                level: 'CRITICAL',
                source: 'EXTERNAL',
                affectedComponents: ['core'],
                mitigations: [],
                references: [],
            });
            c0di3.registerThreat({
                title: 'High Threat',
                description: 'A high threat',
                level: 'HIGH',
                source: 'OSINT',
                affectedComponents: ['api'],
                mitigations: [],
                references: [],
            });
            c0di3.registerThreat({
                title: 'Low Threat',
                description: 'A low threat',
                level: 'LOW',
                source: 'ASTRO',
                affectedComponents: ['utils'],
                mitigations: [],
                references: [],
            });
        });
        it('should get threats by level', () => {
            const critical = c0di3.getThreatsByLevel('CRITICAL');
            const high = c0di3.getThreatsByLevel('HIGH');
            const low = c0di3.getThreatsByLevel('LOW');
            expect(critical).toHaveLength(1);
            expect(high).toHaveLength(1);
            expect(low).toHaveLength(1);
        });
        it('should get critical threats', () => {
            const critical = c0di3.getCriticalThreats();
            expect(critical).toHaveLength(2); // CRITICAL + HIGH
            expect(critical.some((t) => t.level === 'CRITICAL')).toBe(true);
            expect(critical.some((t) => t.level === 'HIGH')).toBe(true);
        });
    });
    describe('Incident Management', () => {
        let threatId;
        beforeEach(() => {
            const threat = c0di3.registerThreat({
                title: 'Test Threat',
                description: 'A test threat',
                level: 'HIGH',
                source: 'TEST',
                affectedComponents: [],
                mitigations: [],
                references: [],
            });
            threatId = threat.id;
        });
        it('should create an incident from a threat', () => {
            const incident = c0di3.createIncident(threatId, 'HIGH');
            expect(incident.id).toBeDefined();
            expect(incident.threatId).toBe(threatId);
            expect(incident.status).toBe('OPEN');
            expect(incident.severity).toBe('HIGH');
            expect(incident.timeline).toHaveLength(1);
        });
        it('should add events to incident timeline', () => {
            const incident = c0di3.createIncident(threatId, 'HIGH');
            c0di3.addIncidentEvent(incident.id, 'Investigation started');
            c0di3.addIncidentEvent(incident.id, 'Findings confirmed');
            const updated = c0di3.getIncident(incident.id);
            expect(updated?.timeline).toHaveLength(3); // Initial + 2 new
            expect(updated?.timeline[1].event).toBe('Investigation started');
        });
        it('should update incident status', () => {
            const incident = c0di3.createIncident(threatId, 'HIGH');
            c0di3.updateIncidentStatus(incident.id, 'INVESTIGATING');
            const updated = c0di3.getIncident(incident.id);
            expect(updated?.status).toBe('INVESTIGATING');
            expect(updated?.timeline.some((e) => e.event.includes('INVESTIGATING'))).toBe(true);
        });
        it('should get open incidents', () => {
            c0di3.createIncident(threatId, 'HIGH');
            const incident2 = c0di3.createIncident(threatId, 'MEDIUM');
            c0di3.updateIncidentStatus(incident2.id, 'RESOLVED');
            const open = c0di3.getOpenIncidents();
            expect(open).toHaveLength(1);
            expect(open[0].status).toBe('OPEN');
        });
    });
    describe('Knowledge Base', () => {
        it('should add knowledge entry', () => {
            const entry = c0di3.addKnowledgeEntry({
                category: 'TECHNIQUE',
                name: 'SQL Injection',
                description: 'Injection attack technique',
                relatedThreats: [],
                relatedTactics: [],
                platforms: ['web'],
                references: ['https://example.com'],
                mitreTechnique: 'T1190',
            });
            expect(entry.id).toBeDefined();
            expect(entry.name).toBe('SQL Injection');
        });
        it('should get knowledge by MITRE technique', () => {
            c0di3.addKnowledgeEntry({
                category: 'TECHNIQUE',
                name: 'SQL Injection',
                description: 'Test',
                relatedThreats: [],
                relatedTactics: [],
                platforms: [],
                references: [],
                mitreTechnique: 'T1190',
            });
            c0di3.addKnowledgeEntry({
                category: 'TECHNIQUE',
                name: 'XSS',
                description: 'Test',
                relatedThreats: [],
                relatedTactics: [],
                platforms: [],
                references: [],
                mitreTechnique: 'T1190',
            });
            const entries = c0di3.getKnowledgeByMitreTechnique('T1190');
            expect(entries).toHaveLength(2);
        });
        it('should get knowledge by category', () => {
            c0di3.addKnowledgeEntry({
                category: 'TECHNIQUE',
                name: 'SQL Injection',
                description: 'Test',
                relatedThreats: [],
                relatedTactics: [],
                platforms: [],
                references: [],
            });
            c0di3.addKnowledgeEntry({
                category: 'TACTIC',
                name: 'Initial Access',
                description: 'Test',
                relatedThreats: [],
                relatedTactics: [],
                platforms: [],
                references: [],
            });
            const techniques = c0di3.getKnowledgeByCategory('TECHNIQUE');
            const tactics = c0di3.getKnowledgeByCategory('TACTIC');
            expect(techniques).toHaveLength(1);
            expect(tactics).toHaveLength(1);
        });
    });
    describe('Summary', () => {
        it('should provide threat intelligence summary', () => {
            c0di3.registerThreat({
                title: 'Critical',
                description: 'Test',
                level: 'CRITICAL',
                source: 'TEST',
                affectedComponents: [],
                mitigations: [],
                references: [],
            });
            c0di3.registerThreat({
                title: 'High',
                description: 'Test',
                level: 'HIGH',
                source: 'TEST',
                affectedComponents: [],
                mitigations: [],
                references: [],
            });
            const summary = c0di3.getSummary();
            expect(summary.totalThreats).toBe(2);
            expect(summary.threatsBy.CRITICAL).toBe(1);
            expect(summary.threatsBy.HIGH).toBe(1);
            expect(summary.totalIncidents).toBe(0);
        });
    });
});
//# sourceMappingURL=threat-intelligence.test.js.map