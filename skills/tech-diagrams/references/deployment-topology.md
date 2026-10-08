# Deployment Topology Diagram Reference

> Deep reference for Deployment Topology diagrams showing how software maps to infrastructure. Supplements `diagram-types.md` with guidance from C4 deployment diagrams, cloud provider conventions, GCP resource hierarchy, Kubernetes patterns, and UML deployment notation.
>
> **Sources**: C4 model deployment diagrams (Simon Brown), Google Cloud Architecture Center deployment archetypes, GCP landing zone resource hierarchy, Azure/AWS reference architectures, UML 2.x deployment notation, Kubernetes architecture conventions.

## What is a Deployment Topology Diagram?

A deployment topology shows **where software runs within infrastructure** — mapping logical containers/services from architecture diagrams to physical or virtual deployment targets. It answers: "What runs where, and how is it organized?"

- **Scope**: One deployment environment (dev, staging, prod) for one or more software systems
- **Primary technique**: Nested containment — infrastructure nodes contain software instances
- **Audience**: DevOps, infrastructure engineers, operations teams, architects
- **Key distinction**: Separate from container diagrams (which are deployment-agnostic) per Simon Brown's explicit guidance

## When to Use

- **Infrastructure planning**: Showing GCP/Azure/AWS resource organization
- **Environment documentation**: What's deployed where in production vs. dev
- **Capacity planning**: Instance counts, scaling configs, regional placement
- **Operations handoff**: Giving ops teams a map of what they're managing
- **Migration planning**: Showing target infrastructure for a cloud migration

## Core Elements

| Element | Visual Treatment | Description |
|---------|-----------------|-------------|
| **Deployment Node** | Nested rectangle with label | Where software runs (region, zone, project, cluster, VM, container) |
| **Infrastructure Node** | Rectangle with distinct icon | Supporting infra that isn't a deployment target (load balancer, DNS, firewall, CDN) |
| **Software Instance** | Rounded rectangle inside a deployment node | Actual deployed service — maps from C2 containers |
| **Communication Path** | Labeled arrow between nodes | Network connection with protocol label |
| **Scaling Annotation** | Badge or text annotation | "x3", "min 1 / max 10", "2 vCPU, 4 GiB" |

## Composition Rules

### Containment Hierarchy
The key visual principle is **nested rectangles** showing containment:

```
GCP Organization
  └── Folder (environment or team)
       └── Project (billing/IAM boundary)
            ├── Cloud Run service
            ├── GKE Cluster
            │    └── Namespace
            │         └── Deployment (with replicas annotation)
            ├── Cloud SQL instance
            ├── Pub/Sub topic
            └── Cloud Storage bucket
```

### Environment Handling
**One diagram per environment** (C4 recommendation). When environments differ substantially, create separate diagrams. Options for showing multiple environments:

| Approach | When to Use |
|----------|-------------|
| **Separate diagrams** per environment | Environments differ substantially (different services, regions) |
| **Single representative** with differences table | Environments follow the same topology at different scale |
| **Side-by-side simplified columns** | Differences between environments are the focus |

### Mapping from C2
- Each container from the C2 diagram becomes a **named service instance** within a deployment node
- Use the same name as the C2 container, plus the deployment context
- External systems from C2 reappear outside the infrastructure boundary

### Scaling Representation
Show replicas/scaling without drawing N copies:
- **Single instance with badge**: Draw one service with "x3" or "replicas: 3" annotation
- **Stacked offset rectangles**: 2–3 slightly offset boxes with count annotation
- **Auto-scaling range**: "min 1 / max 10" text annotation
- **Dashed boundary**: Like AWS Auto Scaling Group convention

## Density Limits

| Metric | Recommended | Hard Ceiling |
|--------|-------------|--------------|
| Nesting depth | 3–4 levels | 5 levels |
| Services per project/namespace | 4–6 | 8 |
| Total elements per diagram | 15–20 | 25 |
| Communication paths (arrows) | 8–12 | 18 |
| Regions/zones shown | 1–2 | 3 |

If exceeding limits, split by:
- **Subsystem**: Frontend deployment, backend deployment, data tier deployment
- **Layer**: Compute topology vs. data topology
- **Region**: One diagram per region

## Layout Rules

### Nesting Structure
- **Outermost boundary**: Cloud organization or region
- **Second level**: Folders, projects, or accounts
- **Third level**: Clusters, VPCs, namespaces
- **Innermost**: Individual service instances
- Each nesting level uses a distinct border style (solid, dashed) or subtle fill shade

### Spatial Arrangement
- **Top-to-bottom** or **left-to-right** flow from external users through infrastructure layers
- External traffic enters from the **left or top**
- Load balancers and gateways sit at infrastructure boundaries
- Data stores at the **bottom or right**
- Supporting infrastructure (DNS, CDN, monitoring) along the **top or bottom edge**

### Regional/Zonal Layout
- Regions as large containing rectangles
- Zones as sub-rectangles within regions
- Redundant services shown in each zone (don't abbreviate — each zone gets its own copy)
- Failover regions in lighter/dashed treatment

### GCP-Specific Conventions
For GCP deployment topologies:
- **Organization** → **Folder** → **Project** nesting
- Use GCP product icons alongside text labels
- Label projects with actual project IDs where known
- Show VPC/subnet boundaries only when network topology is relevant (otherwise keep in separate network diagram)

## Arrow Conventions

- **Labeled with protocol**: "HTTPS", "gRPC", "TCP/5432", "Pub/Sub"
- Solid arrows for synchronous communication
- Dashed arrows for async (event-driven, message queue)
- Show direction: arrows point from caller to callee
- **Don't show co-location as communication**: Services on the same cluster don't necessarily talk to each other

## Service Configuration Annotations

How to show config without cluttering:
- **Inside the service box**: Service name (line 1), key config (line 2–3)
  - Example: "Cloud Run: agent-service / 2 vCPU, 4 GiB, min 1 / max 10"
- **Technology tags**: Small text or icon below the service name ("Python 3.12", "Node.js 20")
- **Supplementary table**: Map service name → instance type, scaling config, region

## Title Format

`PROJECT — Deployment Topology: [Environment Name]`

## Relationship to Other Diagrams

| Diagram | Shows | Overlap |
|---------|-------|---------|
| **C2 Container** | Logical building blocks (deployment-agnostic) | Same containers appear, but no infrastructure detail |
| **Network/Security** | Traffic flow, firewalls, subnets | Both show regions/zones, but network focuses on routing |
| **Deployment Topology** | What runs where on what infrastructure | Maps C2 containers to specific infra |

**Do not merge C2 and Deployment** — keep them separate per C4 model guidance.

## Anti-Patterns

| Anti-Pattern | Fix |
|-------------|-----|
| Merging container and deployment diagrams | Keep C2 (logical) and deployment (physical) separate |
| Generic/theoretical infrastructure | Name actual projects, regions, service instances |
| Mixed abstraction levels | Keep consistent granularity — don't mix individual functions with high-level gateways |
| Unlabeled connections | Every arrow needs a protocol label |
| Misleading nesting | Don't nest a service inside a boundary it doesn't belong to |
| Showing all environments in one diagram | One diagram per environment; use a differences table for comparison |
| Co-location implying communication | Being on the same cluster doesn't mean services talk |
| Drawing N copies for replicas | Use scaling annotations instead |
| No legend | Include a legend for icons, line styles, and nesting conventions |
| Trying to show everything | Scope to one environment, one subsystem if needed |
| Network detail in deployment diagram | Keep VPC/subnet/firewall details in a separate network diagram |
