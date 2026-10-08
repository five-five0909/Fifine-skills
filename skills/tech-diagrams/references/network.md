# Network & Security Diagram Reference

> Deep reference for Network & Security diagrams. Supplements `diagram-types.md` with guidance from cloud provider networking documentation (GCP VPC, Azure VNet, AWS VPC), Zero Trust architecture principles, NIST 800-207, and practitioner field experience with hub-and-spoke, private endpoint, and perimeter security patterns.
>
> **Sources**: Google Cloud Architecture Center, Azure Well-Architected Framework (Networking pillar), AWS VPC documentation, NIST SP 800-207 (Zero Trust), cloud.google.com/architecture, CIS Benchmarks, cognitive load research (Sweller, Mayer & Moreno).

## What is a Network & Security Diagram?

A network & security diagram shows **how traffic flows through network boundaries, trust zones, and access controls** to reach protected resources. It answers: "How is this system secured, and what path does traffic take from an external user to an internal resource?"

- **Scope**: One environment's network topology and security posture (e.g., production VNet/VPC, hub-and-spoke layout, ingress/egress paths)
- **Primary elements**: Network zones, trust boundaries, subnets, private endpoints, firewalls, NAT gateways, VPN gateways, DNS zones, security groups
- **Audience**: Networking engineers, security architects, compliance reviewers, cloud platform teams
- **C4 alignment**: Orthogonal to C4 — this is a deployment/infrastructure view, not a software architecture view. Network diagrams show *where* and *how* traffic flows; C4 shows *what* software exists.

## When to Use

- Documenting the **network topology** of a cloud deployment (VPC/VNet layout, subnets, peering)
- Showing **ingress and egress paths** — how external users reach internal services and how internal services reach the internet
- Communicating **trust boundaries** and **security controls** to compliance or security review boards
- Explaining **private connectivity** patterns (Private Link/Private Endpoints, VPN, ExpressRoute/Interconnect)
- Demonstrating that **public network access is disabled** and all traffic flows through private channels
- Visualizing **access chains** — the full sequence of security controls a request traverses (conditional access, VPN, firewall, private endpoint, resource)
- Documenting **hub-and-spoke** or **mesh** network architectures with shared services

## Core Elements

| Element | Visual Treatment | Description |
|---------|-----------------|-------------|
| **Network Zone / VPC / VNet** | Colored zone rectangle (light blue for primary, light green for hub/shared) | Top-level network boundary — contains subnets and resources |
| **Subnet** | Nested zone rectangle with CIDR label | Layer within a VPC/VNet — groups resources by function or security posture |
| **Trust Boundary** | Dashed gray or red border | Demarcation between trust levels (public internet, DMZ, private network, management plane) |
| **Firewall / NSG / Security Group** | Product card with shield icon | Stateful or stateless packet filtering at zone or subnet boundaries |
| **Private Endpoint** | Product card with green (#34A853) accent or green zone background | Private IP address that connects to a PaaS service over the backbone network |
| **NAT Gateway** | Product card with outbound arrow icon | Enables outbound internet access for private subnet resources without inbound exposure |
| **VPN Gateway** | Product card with lock/tunnel icon | Encrypted tunnel between on-premises or remote networks and cloud VPC/VNet |
| **Load Balancer** | Product card with load balancer icon | Traffic distribution — external (public-facing) or internal (private) |
| **DNS Zone** | Product card or annotation with domain label | Name resolution — private DNS zones for private endpoint hostname resolution |
| **Resource** | Standard product card | The compute, storage, or PaaS service being protected (sits inside a subnet or behind a private endpoint) |
| **Blocked Path** | Red (#EA4335) dashed line with X marker or strikethrough | Explicitly denied traffic — shows what is NOT allowed |
| **Allowed Path** | Solid blue (#4285F4) line with arrowhead | Permitted traffic flow through security controls |

## Density Limits

| Metric | Recommended | Hard Ceiling |
|--------|-------------|--------------|
| Network zones (VPC/VNet) | 2–3 | 5 |
| Subnets per zone | 3–5 | 7 |
| Total elements (all types) | 15–20 | 30 |
| Trust boundaries | 2–4 | 6 |
| Arrows (traffic flows) | 10–15 | 25 |

The 7 +/- 2 heuristic applies: any single view should not require the viewer to hold more than ~7 distinct conceptual chunks in working memory. Network diagrams are inherently dense — be aggressive about splitting.

### When to Split

- **>3 VPCs/VNets** → split into "Hub Network" and "Spoke Network" diagrams
- **Ingress + egress are both complex** → separate "Inbound Access" and "Outbound Egress" diagrams
- **Multiple environments** (dev, staging, prod) → one diagram per environment, with a topology overview showing how they connect
- **DNS is complex** → separate "DNS Resolution Flow" diagram
- **Firewall rules are the focus** → separate "Firewall Rules Matrix" (tabular, not a diagram)

## Zone and Swim Lane Conventions

Network diagrams use **horizontal swim lanes** or **nested zones** to communicate trust levels and network boundaries.

### Swim Lane Pattern (Left-to-Right Trust Escalation)

```
| External / Internet | DMZ / Edge | Private Network | Management Plane |
|      (untrusted)    | (semi-trust)|    (trusted)    |   (privileged)   |
```

- **Leftmost lane**: External users, the internet, partner networks — untrusted
- **Second lane**: Edge services — load balancers, WAF, API gateways, VPN termination
- **Third lane**: Private network — application subnets, data subnets, private endpoints
- **Rightmost lane**: Management plane — bastion hosts, admin access, key vaults, monitoring

Each lane's background color communicates trust level:
- **Pink/salmon (#FCE8E6)**: Untrusted / external / internet
- **Light yellow (#FEF7E0)**: Semi-trusted / DMZ / edge
- **Light blue (#E8F0FE)**: Trusted / private network
- **Light green (#E6F4EA)**: Hub / shared services / management

### Nested Zone Pattern (Containment Hierarchy)

```
Organization
  └─ Project / Subscription / Account
       └─ VPC / VNet
            └─ Region
                 └─ Subnet (with CIDR)
                      └─ Resources
```

Zones nest inside each other. Use progressively lighter background shades for deeper nesting. Label each zone in the top-left corner with:
- Zone type (VPC, Subnet, Region)
- Name (e.g., "prod-vnet-eastus2")
- CIDR notation where applicable (e.g., "10.0.0.0/16")

## Trust Boundary Representation

Trust boundaries are the **most important element** in a network & security diagram. They answer: "Where does the security posture change?"

### Visual Treatment
- **Dashed border** — heavier weight (2px) than standard zone borders
- **Red dashed (#EA4335)** for critical trust boundaries (internet-to-private, public-to-internal)
- **Gray dashed (#9AA0A6)** for internal trust boundaries (subnet-to-subnet, spoke-to-hub)
- **Label every trust boundary** — "Internet Boundary", "VNet Peering Boundary", "On-Premises Boundary"

### Common Trust Boundaries
| Boundary | What Crosses It | Controls |
|----------|----------------|----------|
| Internet → Cloud | External user traffic | WAF, DDoS protection, external load balancer, conditional access |
| Cloud → On-Premises | Hybrid connectivity | VPN Gateway, ExpressRoute/Interconnect, firewall rules |
| Hub → Spoke | Cross-VNet traffic | VNet peering, route tables, NSG/firewall rules |
| Subnet → Subnet | Lateral movement | NSGs, security groups, micro-segmentation |
| User → PaaS Service | Data plane access | Private endpoint, service firewall, RBAC, managed identity |
| Management Plane | Admin access | Bastion, JIT access, PIM, audit logging |

### Annotation at Trust Boundaries
At each trust boundary crossing, annotate the **security control** that gates passage:
- Firewall rule name or policy
- NSG/security group reference
- "publicNetworkAccess: disabled"
- Authentication mechanism (managed identity, API key, certificate)
- Encryption in transit (TLS 1.2+, IPsec)

## Private Endpoint Visualization

Private endpoints are a critical pattern in modern cloud security — they bring PaaS services into the private network.

### Visual Rules
- Show the private endpoint as a **card with a green accent** or place it inside a **green-tinted zone** to visually distinguish it from regular compute resources
- Position the private endpoint **inside the subnet** where it is deployed
- Draw an arrow from the private endpoint to the PaaS service it connects to, labeled "Private Link"
- Annotate "publicNetworkAccess: disabled" on the PaaS service card
- Show the **private DNS zone** that resolves the service's public FQDN to the private IP

### Pattern
```
[Subnet: private-endpoints (10.0.4.0/24)]
   └─ Private Endpoint (storage-pe) ──Private Link──→ Storage Account
   └─ Private Endpoint (sql-pe)     ──Private Link──→ SQL Database
   └─ Private Endpoint (kv-pe)      ──Private Link──→ Key Vault

[Private DNS Zone: privatelink.blob.core.windows.net]
   └─ Resolves: mystorageacct.blob.core.windows.net → 10.0.4.5
```

## NAT Gateway Visualization

NAT gateways provide **outbound internet access** for resources in private subnets without exposing inbound paths.

### Visual Rules
- Place the NAT gateway **at the subnet boundary**, between the private subnet and the internet
- Arrow direction: Private resource → NAT Gateway → Internet (outbound only)
- Label the arrow: "Outbound HTTPS (egress)" or "Outbound to [specific service]"
- Annotate that **no inbound path exists** through the NAT gateway — use a blocked-path marker on any attempted inbound arrow
- Show the public IP or IP range associated with the NAT gateway if IP allowlisting is relevant

## VPN and Hybrid Connectivity

### VPN Gateway Pattern
```
[On-Premises Network]
   └─ On-Prem Firewall ──IPsec VPN Tunnel──→ VPN Gateway ──→ [Cloud VNet]
```

- Show the VPN tunnel as a **dashed blue line with lock icon** or label "IPsec/IKEv2"
- Place VPN gateways in a dedicated **gateway subnet** (cloud-side requirement for Azure, GCP, AWS)
- Annotate tunnel bandwidth, BGP peering, or route propagation if relevant

### ExpressRoute / Cloud Interconnect / Direct Connect
- Show as a **thick solid line** (heavier than standard connectors) to indicate dedicated connectivity
- Label with circuit type and bandwidth: "ExpressRoute 1Gbps" or "Dedicated Interconnect 10Gbps"
- Differentiate from internet paths visually — dedicated connectivity is premium, should look premium

## Firewall and Security Group Annotation

### Firewall Rules
- Do NOT attempt to show every firewall rule on the diagram — it will be unreadable
- Show **firewall appliances/services** as product cards at trust boundaries
- Annotate the **policy intent**, not individual rules: "Allow HTTPS from VPN subnet only", "Deny all inbound from internet"
- For detailed rule sets, reference a separate table: "See Firewall Rules Appendix"

### Security Groups / NSGs
- Show as **annotations on subnet boundaries** or as a small shield icon at the subnet perimeter
- Label with the policy intent: "NSG: Allow 443 from 10.0.1.0/24"
- For complex NSG configurations, use a **tabular format** alongside the diagram:

| NSG | Direction | Port | Source | Destination | Action |
|-----|-----------|------|--------|-------------|--------|
| app-nsg | Inbound | 443 | 10.0.1.0/24 | 10.0.2.0/24 | Allow |
| app-nsg | Inbound | * | Internet | 10.0.2.0/24 | Deny |

## Access Chain Visualization

One of the most valuable things a network diagram can show is the **complete access chain** — the full path a request takes from an external user to a protected resource, passing through every security control.

### Pattern
```
User → Conditional Access (MFA, device compliance)
     → VPN Gateway (IPsec tunnel)
     → Hub VNet Firewall (policy inspection)
     → VNet Peering (hub → spoke)
     → NSG (port 443 only)
     → Private Endpoint
     → PaaS Resource (publicNetworkAccess: disabled)
```

### Visual Rules
- Lay out the access chain **left-to-right** as a linear progression
- Number each step with blue circles (Google Cloud pattern)
- At each security control, annotate what is checked/enforced
- Use **green checkmarks** or **allowed** indicators at each control that passes
- At the end (the protected resource), annotate "publicNetworkAccess: disabled" to show the resource is sealed

### Blocked/Denied Path Representation
- Show **explicitly denied paths** alongside the allowed chain
- Use **red dashed lines (#EA4335)** with an X marker or "DENIED" label
- Common denied paths to show:
  - Direct internet → PaaS resource (blocked by "publicNetworkAccess: disabled")
  - Direct internet → private subnet (blocked by NSG/firewall)
  - Unauthorized lateral movement (blocked by micro-segmentation)
- Denied paths are as informative as allowed paths — they answer "What does NOT work?"

## DNS Zone and Resolution Flow

### When to Show DNS
- When **private DNS zones** are part of the architecture (Private Link/Endpoint scenarios)
- When **split-horizon DNS** is used (different resolution for internal vs external clients)
- When **DNS forwarding** or **conditional forwarding** affects connectivity

### Visual Rules
- Show DNS zones as **annotation boxes** or **product cards** with domain names
- Draw resolution arrows as **dashed lines** (lighter than data flow arrows) labeled "resolves"
- Show the resolution chain: Client → DNS Resolver → Private DNS Zone → Private IP
- Annotate the FQDN and the private IP it resolves to

### Pattern
```
Client queries: storageacct.blob.core.windows.net
   → Azure DNS (or custom resolver)
   → Private DNS Zone: privatelink.blob.core.windows.net
   → Returns: 10.0.4.5 (private endpoint IP)
   → Traffic flows to private endpoint on private network
```

## Hub-and-Spoke Topology

The most common enterprise cloud network pattern.

### Visual Rules
- **Hub VNet/VPC** in the center — colored with green (#E6F4EA) zone background to indicate shared services
- **Spoke VNets/VPCs** arranged around the hub — colored with blue (#E8F0FE) zone backgrounds
- **Peering connections** shown as lines between hub and each spoke, labeled "VNet Peering" or "VPC Peering"
- Hub contains shared services: firewall, VPN gateway, bastion, DNS, monitoring
- Each spoke contains workload-specific resources

### Layout Pattern
```
                    [On-Premises]
                         |
                    VPN Gateway
                         |
    [Spoke A] ── Peering ── [Hub VNet] ── Peering ── [Spoke B]
    (workload A)         │  - Firewall            (workload B)
                         │  - Bastion
                         │  - DNS
                    Peering
                         │
                    [Spoke C]
                    (workload C)
```

- Alternatively, lay out left-to-right: On-Prem → Hub → Spokes (for swim-lane alignment)
- Show that spoke-to-spoke traffic **transits through the hub firewall** — do not imply direct spoke-to-spoke connectivity unless it exists

### Hub Contents
Always show in the hub:
- Firewall or NVA (network virtual appliance)
- VPN/ExpressRoute gateway
- Bastion host (if used)
- Private DNS zones (if centralized)
- Route tables / UDRs that force traffic through the firewall

## Cloud-Specific Patterns

### GCP VPC
- **Shared VPC** model: Host project owns the VPC, service projects deploy resources into it
- Show the host project as the containing zone, service projects as nested zones within shared subnets
- **Firewall rules** are VPC-level (not subnet-level) — show at the VPC boundary
- **Cloud NAT** per-region — place at the regional boundary
- **Private Google Access** and **Private Service Connect** for Google API access
- Subnets are **regional** (not zonal) — label with region name

### Azure VNet
- **Hub-and-spoke** with Azure Firewall in the hub is the canonical pattern
- **NSGs** are subnet-level — show at subnet boundaries
- **Private Endpoints** and **Private DNS Zones** for PaaS connectivity
- **UDRs (User Defined Routes)** force traffic through the firewall — annotate on route arrows
- **Service Endpoints** vs **Private Endpoints** — prefer Private Endpoints (stronger isolation)
- Subnets within a VNet are within a **single region** — label with region

### AWS VPC
- **Transit Gateway** replaces simple peering for hub-and-spoke at scale — show as a central routing element
- **Security Groups** are instance-level (stateful); **NACLs** are subnet-level (stateless) — show both if both are relevant
- **VPC Endpoints** (Interface and Gateway types) for AWS service access
- **PrivateLink** for cross-account or cross-VPC service exposure
- Subnets are **availability-zone-scoped** — label with AZ

## Subnet and CIDR Notation Conventions

### Always Include
- Subnet name and purpose (e.g., "app-subnet", "data-subnet", "gateway-subnet")
- CIDR block (e.g., "10.0.1.0/24")
- Number of available IPs if relevant for capacity planning

### Naming Pattern in Labels
```
app-subnet
10.0.1.0/24
(251 usable IPs)
```

### CIDR Layout Convention
- Show the **VPC/VNet CIDR** on the outermost zone label (e.g., "10.0.0.0/16")
- Show **subnet CIDRs** on each nested subnet zone (e.g., "10.0.1.0/24")
- Make it visually obvious that subnet CIDRs are subsets of the VPC CIDR
- If non-overlapping ranges matter for peering, annotate this explicitly

### Address Space Table
For complex deployments, include an address space table alongside the diagram:

| VNet/VPC | CIDR | Subnet | CIDR | Purpose |
|----------|------|--------|------|---------|
| hub-vnet | 10.0.0.0/16 | GatewaySubnet | 10.0.0.0/27 | VPN/ER Gateway |
| hub-vnet | 10.0.0.0/16 | AzureFirewallSubnet | 10.0.1.0/26 | Firewall |
| spoke-prod | 10.1.0.0/16 | app-subnet | 10.1.1.0/24 | Application tier |
| spoke-prod | 10.1.0.0/16 | data-subnet | 10.1.2.0/24 | Data tier |

## Layout Rules

### Primary Flow Direction
- **Left-to-right**: External access → Network boundary → Internal resources
- Or **top-to-bottom**: Internet at top → Edge → Private → Data stores at bottom
- Choose one and be consistent within the diagram

### Spatial Arrangement
- **Leftmost / Top**: External users, internet, on-premises networks (untrusted)
- **Center-left**: Edge security — VPN gateway, firewall, WAF, external load balancer
- **Center**: Application subnets, compute resources (private network)
- **Center-right**: Data subnets, private endpoints, PaaS services
- **Rightmost / Bottom**: Management plane — bastion, key vault, monitoring
- **Below or separate band**: DNS zones, route tables (supporting infrastructure)

### Arrow Routing
- **Orthogonal only** — horizontal and vertical segments, 90-degree turns
- **No crossings** — if arrows cross, the layout needs rearranging. This is critical in network diagrams where crossing arrows falsely imply interconnection.
- **Traffic direction matters** — ingress flows left-to-right, egress flows right-to-left (or use dashed lines for egress)
- **Blocked paths** use red dashed lines — visually distinct from allowed traffic

### Whitespace
- Generous spacing (minimum 40px between elements)
- Network diagrams are dense by nature — err on the side of more whitespace, not less
- Use zone backgrounds to group elements rather than cramming cards close together
- Leave clear corridors for arrow routing between zones

## Common Anti-Patterns

| Anti-Pattern | Why It's Bad | Fix |
|---|---|---|
| **Showing every firewall rule on the diagram** | Unreadable — 50+ rules don't fit visually | Show policy intent; reference a rules table |
| **No trust boundaries** | Reader can't distinguish public from private | Add dashed borders at every trust level change |
| **All resources in one flat zone** | Implies everything is at the same trust level | Nest resources in subnets within VPCs/VNets |
| **Missing CIDR notation** | Network engineers can't validate address space | Add CIDR to every VPC/VNet and subnet |
| **Bidirectional arrows** | Obscures initiator and flow direction | Unidirectional arrows — one for request, optionally one for response |
| **Only showing allowed paths** | Doesn't prove security — "What can't happen?" is as important | Add red blocked-path markers for explicitly denied traffic |
| **VPN/firewall shown as decorative icon** | No context on what it controls | Show as product card with policy annotation |
| **Mixing logical and physical topology** | Confuses software components with network elements | Separate network diagram from C2 container diagram |
| **Subnets without purpose labels** | "Subnet A" tells the reader nothing | Label by function: "app-subnet", "data-subnet", "gateway-subnet" |
| **DNS omitted when private endpoints are shown** | Reader can't understand how name resolution works | Add private DNS zone and resolution annotation |
| **Public IPs on resources without explanation** | Implies exposure — triggers security review flags | Annotate why a public IP exists, or show that it's behind a WAF/LB |
| **No legend** | Readers guess at what colors, dashes, and icons mean | Always include a legend |
| **Hub-and-spoke with no route annotations** | Reader assumes direct spoke-to-spoke connectivity | Show UDRs and annotate "traffic via hub firewall" |
| **>30 elements on one diagram** | Cognitive overload | Split into sub-diagrams by concern |
| **Colors as only differentiator** | Fails in B&W print, inaccessible to colorblind reviewers | Use shape, label, position, and line style as redundant signals |

## Common Scenarios

### Scenario 1: Private PaaS Access
Show how an application in a private subnet accesses a PaaS service (database, storage, key vault) through private endpoints with no public internet exposure.

**Key elements**: Application subnet → Private endpoint subnet → Private endpoint → PaaS service (publicNetworkAccess: disabled) + Private DNS zone for resolution.

### Scenario 2: User Access Chain
Show the complete path from an external user to an internal application, traversing every security control.

**Key elements**: User → Conditional Access (MFA, device compliance) → VPN Gateway → Hub Firewall → VNet Peering → Spoke NSG → Application (private subnet). Show the denied path: User → Internet → Application (DENIED — publicNetworkAccess: disabled).

### Scenario 3: Hub-and-Spoke Topology
Show a multi-spoke enterprise network with centralized security services.

**Key elements**: Hub VNet (firewall, VPN gateway, bastion, DNS) + 2-3 spoke VNets (workload subnets) + peering connections + on-premises connectivity. Show that spoke-to-spoke traffic transits hub firewall.

### Scenario 4: Outbound Egress Control
Show how internal resources reach the internet or external APIs through controlled egress.

**Key elements**: Private subnet → NAT Gateway (or firewall with egress rules) → Internet / External API. Annotate egress IP range for allowlisting. Show denied path: Private subnet → Direct internet (DENIED — no default internet route).

### Scenario 5: Multi-Cloud or Hybrid Connectivity
Show connectivity between cloud environments or between cloud and on-premises.

**Key elements**: Cloud VPC/VNet → VPN Gateway / Interconnect → On-Premises network. Show firewall rules at each boundary. Annotate tunnel encryption and bandwidth.

### Scenario 6: DNS Resolution with Private Endpoints
Show how DNS queries for PaaS services resolve to private IPs instead of public IPs.

**Key elements**: Client → DNS Resolver → Private DNS Zone → Private IP. Show the split-horizon: external clients resolve to public IP, internal clients resolve to private endpoint IP.

## Required Metadata

Every network & security diagram must include:

1. **Title**: `PROJECT — Network & Security` or `PROJECT — Network: [Specific Focus]`
2. **Legend**: Explain zone colors (trust levels), line styles (allowed vs blocked, VPN vs peering), icons, and any annotations
3. **Environment label**: Which environment this represents (production, staging, development)
4. **Region/location**: Cloud region(s) depicted

## Checklist

Before finalizing a network & security diagram, verify:

- [ ] **Single environment or topology** — diagram shows one coherent network view, not everything
- [ ] **Trust boundaries marked** — dashed borders at every trust level change with labels
- [ ] **Every zone labeled** — VPC/VNet name, subnet name, purpose, CIDR notation
- [ ] **Access chain visible** — reader can trace the full path from external user to internal resource
- [ ] **Blocked paths shown** — at least one denied/blocked path to prove security posture
- [ ] **Private endpoints labeled** — service name, "Private Link" annotation, "publicNetworkAccess: disabled" on target
- [ ] **DNS resolution shown** — if private endpoints exist, show how FQDNs resolve to private IPs
- [ ] **Firewall/NSG policy annotated** — intent-level labels, not exhaustive rule lists
- [ ] **No arrow crossings** — rearrange layout if arrows cross
- [ ] **Orthogonal connectors only** — straight lines, 90-degree turns, no diagonals or curves
- [ ] **Total elements within limits** — 15-20 recommended, 30 hard ceiling
- [ ] **Consistent flow direction** — left-to-right or top-to-bottom, not mixed
- [ ] **Colors are not the only differentiator** — shape, label, position provide redundant signals
- [ ] **Legend included** — zone colors, line styles, blocked-path notation explained
- [ ] **Title follows format**: `PROJECT — Network & Security` or `PROJECT — Network: [Focus]`
- [ ] **Environment and region labeled** — reader knows which deployment this represents

## What Separates Mediocre from Excellent

### Mediocre Network Diagram
- Flat layout — all resources at the same visual level with no nesting
- No trust boundaries — reader can't tell public from private
- Missing CIDR notation — network engineers can't validate the design
- Arrows labeled "Connects to" with no protocol or control annotation
- Only shows allowed paths — doesn't prove what's blocked
- DNS omitted — reader can't understand private endpoint name resolution
- No legend — colors and line styles unexplained
- Looks like a C2 container diagram with extra lines

### Excellent Network Diagram
- **Nested zones** communicate the containment hierarchy: VPC → Subnet → Resources
- **Every trust boundary visible and labeled** — reader immediately sees where security posture changes
- **CIDR notation on every subnet** — validates address space at a glance
- **Complete access chain** — traceable from external user through every control to the protected resource
- **Blocked paths explicitly shown** — proves security posture, not just connectivity
- **Private endpoints + DNS zones** — the full private connectivity story
- **Policy annotations** at security controls — what is enforced, not just what exists
- **Clean legend and title** — no guessing about notation
- **Showable to a security auditor** — they can validate the posture without a verbal walkthrough
