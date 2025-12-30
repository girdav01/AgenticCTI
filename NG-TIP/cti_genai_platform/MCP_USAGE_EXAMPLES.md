# MCP Server Usage Examples

Complete walkthroughs showing how to use the CTI Platform MCP server with Claude.

---

## Example 1: Complete Threat Actor Research

### Scenario
You need to research APT28 and create a comprehensive threat profile.

### Conversation with Claude

**You:** "I need to research APT28. Can you search all our threat intelligence sources and give me a comprehensive report?"

**Claude:** *Uses multiple MCP tools automatically:*
1. `search_threat_intelligence` with query "APT28"
2. `get_opencti_threat_actors` to get detailed info
3. `query_graph_relationships` for APT28
4. `search_misp_events` for recent APT28 activity

**Claude's Response:**
```
Based on my search across all threat intelligence sources:

MISP Sources (15 events):
- Operation targeting European diplomatic entities (2024-11)
- Spear-phishing campaign against NATO partners (2024-10)
- Infrastructure overlaps with previous operations

OpenCTI Intelligence:
- Threat Actor: APT28 (Fancy Bear, Sofacy Group)
- Sophistication: High
- Primary Motivation: Espionage
- Associated TTPs: 23 attack patterns identified

Graph Relationships:
- Uses: Zebrocy, X-Agent, Cannon malware
- Targets: Government, Military, Media sectors
- Infrastructure: 47 C2 domains identified

Knowledge Base Results (8 reports):
- Recent analysis of APT28 evolving tactics
- Attribution analysis linking to previous campaigns
- TTPs comparison with other APT groups

Key Findings:
1. Increased targeting of diplomatic entities
2. New malware variant "Zebrocy 2.0" identified
3. Shift towards supply chain compromises
4. Active in Eastern Europe theater

Recommendations:
- Monitor domains matching infrastructure patterns
- Implement specific detection rules
- Review access controls for targeted sectors
```

**You:** "Can you create STIX objects for this threat actor and their main tools?"

**Claude:** *Uses:*
1. `create_stix_threat_actor` for APT28
2. `create_stix_malware` for Zebrocy, X-Agent, Cannon
3. Creates relationships between objects

**Claude's Response:**
```
Created STIX 2.1 bundle with:

Threat Actor Object:
- ID: threat-actor--[uuid]
- Name: APT28
- Aliases: Fancy Bear, Sofacy Group, Pawn Storm
- Sophistication: strategic
- Resource Level: government

Malware Objects (3):
1. Zebrocy
   - Types: backdoor, trojan
   - First seen: 2015
   
2. X-Agent
   - Types: backdoor
   - Capabilities: keylogging, file collection
   
3. Cannon
   - Types: downloader
   - First seen: 2018

All objects saved with proper relationships and ready for sharing.
```

---

## Example 2: IOC Investigation and Enrichment

### Scenario
Security team found suspicious IP addresses and needs rapid analysis.

### Conversation

**You:** "I have these IPs that triggered alerts: 192.168.1.100, 10.0.0.50, 172.16.1.200. Can you check if they're in our threat intelligence?"

**Claude:** *For each IP:*
1. `search_misp_attributes` with IP value
2. `search_opencti_indicators` with IP value
3. `query_knowledge_base` for IP mentions

**Claude's Response:**
```
IOC Analysis Results:

192.168.1.100:
✅ FOUND in MISP
- Event: "APT28 Infrastructure 2024"
- Context: Command & Control server
- First seen: 2024-11-15
- TLP: AMBER
- To IDS: True
- Associated: Zebrocy malware campaign

❌ NOT FOUND in OpenCTI
❌ NOT FOUND in Knowledge Base

VERDICT: CONFIRMED MALICIOUS - APT28 C2

---

10.0.0.50:
❌ NOT FOUND in MISP
❌ NOT FOUND in OpenCTI
✅ FOUND in Knowledge Base
- Mentioned in threat report "Q3 2024 Network Analysis"
- Context: Internal testing IP
- Classification: Benign

VERDICT: BENIGN - Internal test system

---

172.16.1.200:
✅ FOUND in MISP
✅ FOUND in OpenCTI
- Multiple campaigns: Emotet, Trickbot, Qakbot
- Bulletproof hosting provider
- Active since 2019
- High confidence: 95

VERDICT: CONFIRMED MALICIOUS - Multi-campaign infrastructure

RECOMMENDED ACTIONS:
1. Block 192.168.1.100 and 172.16.1.200 immediately
2. Review logs for any connections to these IPs
3. Check for Zebrocy indicators on systems that contacted 192.168.1.100
4. 10.0.0.50 - verify it's actually internal testing (false positive)
```

**You:** "Add these findings to the graph database and create indicators"

**Claude:** *Uses:*
1. `create_indicator` for each malicious IP
2. `create_relationship` linking IPs to campaigns
3. `add_document_to_knowledge_base` with investigation summary

**Claude's Response:**
```
✅ Created 2 indicator nodes in graph:
- 192.168.1.100 (ipv4-addr) → Linked to APT28
- 172.16.1.200 (ipv4-addr) → Linked to Emotet, Trickbot

✅ Created relationships:
- APT28 --USES--> 192.168.1.100
- Emotet --USES--> 172.16.1.200
- Trickbot --USES--> 172.16.1.200

✅ Added investigation summary to knowledge base for future reference

You can now query these relationships and the investigation will be available for future searches.
```

---

## Example 3: New Malware Campaign Documentation

### Scenario
Analyst discovered a new ransomware campaign and needs to document everything.

### Conversation

**You:** 
```
We discovered a new ransomware campaign. Here are the details:

Campaign Name: DarkCipher 2024
First Seen: 2024-12-01
Targets: Healthcare sector in North America
Ransom: $500K - $2M in Bitcoin

IOCs:
- Hash: d41d8cd98f00b204e9800998ecf8427e
- Domain: dark-cipher[.]onion
- Email: payment@darkcipher[.]com

TTPs:
- Initial access via phishing
- Uses RDP for lateral movement
- Encrypts with AES-256
- Deletes shadow copies

Can you:
1. Add this to knowledge base
2. Create graph nodes for the campaign
3. Generate STIX bundle
4. Cross-reference with similar campaigns
```

**Claude:** *Comprehensive workflow:*

**Step 1: Add to Knowledge Base**
```
✅ Added campaign report to knowledge base
Document ID: dc2024-001
Indexed with metadata:
- Source: Internal Analysis
- Date: 2024-12-29
- TLP: RED
- Sector: Healthcare
```

**Step 2: Create Graph Nodes**
```
✅ Created Campaign node: "DarkCipher 2024"
Properties:
- First seen: 2024-12-01
- Objective: Financial gain
- Sector: Healthcare

✅ Created 3 Indicator nodes:
- File hash (MD5)
- Domain indicator
- Email indicator

✅ Created Malware node: "DarkCipher Ransomware"
Properties:
- Type: Ransomware
- Encryption: AES-256
- Family: New variant

✅ Created relationships:
- Campaign --USES--> DarkCipher Ransomware
- DarkCipher Ransomware --INDICATES--> [IOCs]
- Campaign --TARGETS--> Healthcare
```

**Step 3: Generate STIX Bundle**
```
✅ Created STIX 2.1 bundle with 8 objects:

1. Campaign object
2. Malware object
3. 3x Indicator objects (hash, domain, email)
4. Attack Pattern: Phishing (T1566)
5. Attack Pattern: RDP (T1021.001)
6. Relationship objects

Bundle ID: bundle--[uuid]
Ready for export and sharing
```

**Step 4: Cross-Reference**
```
Searching for similar campaigns...

Found 3 potentially related campaigns:

1. LockBit 3.0 (85% similarity)
   - Same: Healthcare targeting, RDP usage
   - Different: Ransom amounts higher
   - Infrastructure: No overlap

2. BlackCat/ALPHV (78% similarity)
   - Same: AES encryption, shadow copy deletion
   - Different: Uses different initial access
   - Notable: Same geographic targeting

3. Royal Ransomware (72% similarity)
   - Same: Similar TTPs, ransom range
   - Different: Different encryption method
   - Possible: Infrastructure similarities

ASSESSMENT:
DarkCipher appears to be a new operation, possibly inspired by
BlackCat/ALPHV tactics but with distinct infrastructure and methods.
No confirmed attribution to known threat actors yet.

RECOMMENDATIONS:
1. Monitor for infrastructure overlap with BlackCat
2. Share IOCs with healthcare ISACs
3. Create detection rules for TTP combinations
4. Track bitcoin wallets for attribution
```

---

## Example 4: Weekly Threat Intelligence Briefing

### Scenario
Need to generate a weekly brief for leadership.

### Conversation

**You:** "Create a weekly threat intelligence brief for the past 7 days. Include top threats, new campaigns, and trending IOCs."

**Claude:** *Automated briefing generation:*
1. `search_misp_events` with date filter
2. `get_opencti_threat_actors` recent updates
3. `query_knowledge_base` for reports from last week
4. `get_platform_statistics` for metrics

**Claude's Response:**
```
WEEKLY THREAT INTELLIGENCE BRIEF
Week of December 22-29, 2024

EXECUTIVE SUMMARY
=================
- 45 new threat events documented
- 3 active campaigns targeting our industry
- 127 new IOCs added to blocklists
- 2 critical vulnerabilities being exploited

TOP THREATS
===========

1. APT28 Diplomatic Campaign (CRITICAL)
   - Targeting: Government, Diplomatic entities
   - Activity: Increased 40% this week
   - TTPs: Spear-phishing, credential harvesting
   - Recommendation: Enhanced email filtering

2. LockBit Ransomware Surge (HIGH)
   - Targeting: Healthcare, Finance
   - Victims: 12 publicly disclosed
   - Ransom: Average $800K
   - Recommendation: Backup verification

3. Qakbot Resurgence (MEDIUM)
   - Activity: Returning after takedown
   - Method: Malicious Office documents
   - Distribution: Email campaigns
   - Recommendation: Macro blocking

NEW CAMPAIGNS
=============

DarkCipher Ransomware:
- First seen: Dec 1, 2024
- Targets: Healthcare
- Unique aspects: Custom encryption
- Status: Under investigation

ShadowPad Infrastructure Expansion:
- APT41 attributed
- New C2 servers: 23 identified
- Geographic focus: Asia-Pacific
- Action: IP blocks implemented

TRENDING IOCS
=============

Top IOC Categories This Week:
- Phishing domains: 45 new
- Malware hashes: 89 new
- C2 IP addresses: 23 new

Most Active IOCs:
1. evil-domain[.]com (34 detections)
2. 203.0.113.5 (28 detections)
3. a1b2c3d4... hash (19 detections)

MITRE ATT&CK TRENDS
==================

Most Observed Techniques:
1. T1566.001 - Spearphishing (45%)
2. T1021.001 - RDP (32%)
3. T1486 - Data Encryption (28%)

PLATFORM METRICS
===============

MISP:
- Events: 2,847 total (+45 this week)
- Attributes: 18,934 total (+127 this week)
- Organizations: 12 active contributors

OpenCTI:
- Threat Actors: 234 tracked
- Malware Families: 456 documented
- Indicators: 15,789 active

Knowledge Base:
- Documents: 1,245 indexed
- Threat Reports: 89 added this quarter

RECOMMENDATIONS
==============

Immediate Actions:
1. Block trending IOCs (see appendix)
2. Review RDP exposure
3. Update phishing simulations with current tactics

This Week:
1. Patch CVE-2024-XXXXX (critical)
2. Review backup integrity
3. Conduct tabletop for ransomware

This Month:
1. Reassess APT28 controls
2. Update threat model
3. Share IOCs with industry partners

---
Report generated: 2024-12-29 14:30:00 UTC
Next brief: 2025-01-05
```

---

## Example 5: Collaborative Analysis with Data Updates

### Scenario
Multiple analysts working together, using Claude as a shared intelligence assistant.

### Analyst 1

**Analyst 1:** "Search for any Emotet activity in the last month"

**Claude:** 
```
Found 23 Emotet-related events:

MISP Events (15):
- Emotet spam campaigns targeting finance
- New loader variants detected
- C2 infrastructure updates

OpenCTI Indicators (89):
- File hashes: 45
- URLs: 32
- IP addresses: 12

Key Findings:
- Active spam campaign ongoing
- New distribution method via OneNote files
- Collaboration with Qakbot confirmed
```

**Analyst 1:** "Add my analysis to the knowledge base"

```
Analyst 1's Notes on Emotet December 2024:

New tactic observed: Using OneNote attachments instead of 
traditional Office docs. Initial access success rate appears 
higher due to OneNote being less scrutinized by security tools.

Recommendation: Add OneNote file scanning to email gateway.
```

**Claude:** 
```
✅ Added analysis to knowledge base
Document ID: emotet-dec2024-analyst1
Tags: emotet, tactics, onenet, email-security
```

---

### Analyst 2 (Later)

**Analyst 2:** "What do we know about Emotet using OneNote?"

**Claude:** *Finds Analyst 1's notes in knowledge base*
```
From our knowledge base (added 2 hours ago by Analyst 1):

Emotet has been observed using OneNote attachments as a new 
distribution tactic. This appears to be more successful than 
traditional Office documents because OneNote files receive less 
scrutiny from security tools.

Additionally, from MISP:
- 7 samples of OneNote-based Emotet loaders identified
- Detection rate: Initially 12/68 on VirusTotal
- Distribution: Mass email campaigns

Recommendation from team: Add OneNote file scanning to email gateway.

Would you like me to create detection rules or search for more 
technical details?
```

**Analyst 2:** "Yes, and link this to the Emotet malware in our graph"

**Claude:**
```
✅ Created relationship in graph:
   Emotot Malware --DELIVERS-VIA--> OneNote Files

✅ Created indicator node:
   FileType: OneNote (.one)
   Context: Emotet delivery mechanism
   Risk: High

The graph now shows this new TTP is connected to Emotet, making
it discoverable for future analysis and automated queries.
```

---

## Common Patterns and Tips

### 1. Multi-Step Research

**Pattern:** Ask for comprehensive analysis
**Example:** "Research [threat] and give me everything"
**Claude will:** Chain 5-10 tools automatically

### 2. Documentation Workflow

**Pattern:** "Add this to KB and create graph nodes"
**Example:** Analyst findings → Knowledge base + Graph
**Claude will:** Store in RAG + create relationships

### 3. Cross-Referencing

**Pattern:** "Is this related to any known campaigns?"
**Example:** New IOC → Search all sources
**Claude will:** Multi-source lookup + similarity analysis

### 4. Automated Enrichment

**Pattern:** "Enrich this IOC list"
**Example:** List of IPs → Full context for each
**Claude will:** Batch queries + aggregated results

### 5. STIX Generation

**Pattern:** "Create STIX for [entities]"
**Example:** Campaign description → STIX bundle
**Claude will:** Parse + create objects + relationships

---

## Pro Tips

1. **Be Specific**: "Search MISP for APT28" vs "Search for APT28"
2. **Multi-Step**: Ask for end-to-end workflows
3. **Follow-Up**: Claude remembers context, build on previous answers
4. **Exports**: Request STIX bundles for sharing
5. **Updates**: Ask Claude to add findings to KB and graphs

---

**The MCP server makes threat intelligence analysis feel like having a conversation with an expert analyst!** 🎯
