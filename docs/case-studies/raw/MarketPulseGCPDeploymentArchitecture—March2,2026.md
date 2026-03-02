# MarketPulse GCP Deployment Architecture — March 2, 2026

## 1. Executive Summary

This document outlines a secure, cost-effective, and always-on architecture for deploying the MarketPulse n8n workflows (US v7.0 and CN v6.0) on Google Cloud Platform (GCP). The proposed solution leverages the GCP "Always Free" tier to achieve zero monthly costs while ensuring the instance is completely invisible to the public internet, accessible only for administration via a secure tunnel and triggered automatically by a trusted GCP service.

This design directly addresses the user's core requirements:
-   **Always-On Automation:** Eliminate the need for a local browser to be open.
-   **Zero Cost:** Adhere to the "no burn-rate" solo developer constraint.
-   **Maximum Security:** Prevent all unauthorized access and remain hidden from attackers.

## 2. Recommended Architecture: e2-micro VM + Cloud Scheduler

The optimal architecture combines a persistent virtual machine with a serverless cron job service. This hybrid approach provides the stability of an always-on instance with the reliability of a managed scheduler, all within the free tier.

| Component | GCP Service | Configuration | Purpose | Cost |
| :--- | :--- | :--- | :--- | :--- |
| **Compute** | Compute Engine | `e2-micro` VM (0.25 vCPU, 1GB RAM) | Hosts the n8n Docker container 24/7. | $0 |
| **Database** | Docker Container | PostgreSQL (running on the same VM) | Provides persistent storage for workflows and credentials. | $0 |
| **Scheduler** | Cloud Scheduler | Cron Job (e.g., `0 7 * * *`) | Triggers the n8n workflows daily via a secure webhook. | $0 |
| **Security** | Identity-Aware Proxy (IAP) | TCP Tunneling | Provides secure, authenticated SSH access for administration without a public IP. | $0 |
| **Networking** | Virtual Private Cloud (VPC) | Default VPC with custom firewall rules | Isolates the VM from the public internet. | $0 |

### Architectural Diagram

```mermaid
graph TD
    subgraph GCP Project
        subgraph "VPC Network (Private)"
            VM["Compute Engine (e2-micro)<br/>- No Public IP<br/>- Firewall: Deny All Ingress"] -- hosts --> N8N[n8n Docker Container]
            N8N -- uses --> DB[(PostgreSQL Docker Container)]
        end

        subgraph "Management & Triggers"
            SCHEDULER[Cloud Scheduler<br/>"0 7 * * *"] -- "1. Triggers via private webhook" --> N8N
            IAP["Identity-Aware Proxy (IAP)"] -- "3. Secure SSH Tunnel" --> ADMIN(Your Laptop)
            ADMIN -- "4. Manages VM" --> VM
        end
    end

    subgraph Internet
        ATTACKER(Attacker) -.-x VM
        USER(Public User) -.-x VM
    end

    style ATTACKER fill:#ffcccc,stroke:#333,stroke-width:2px
    style USER fill:#ffcccc,stroke:#333,stroke-width:2px
```

## 3. Security Design: Zero Public Exposure

This architecture is designed to be completely invisible and inaccessible from the public internet.

1.  **No Public IP Address:** The `e2-micro` VM will be configured with no external IP address, making it impossible to scan or attack directly from the internet.
2.  **Default-Deny Firewall:** The VPC firewall will be configured to **deny all incoming traffic by default**. The only exception will be a rule allowing SSH traffic (port 22) exclusively through the IAP service.
3.  **Identity-Aware Proxy (IAP):** Administrative access to the VM will be handled via IAP's TCP Tunneling. This requires you to authenticate with your Google Cloud account (`gcloud compute ssh`) before a secure tunnel to the VM is even established. This is far more secure than a traditional VPN or bastion host.
4.  **Secure Webhook Trigger:** Cloud Scheduler will trigger the n8n workflows using a webhook URL. This webhook will be protected with a long, unguessable secret token. The firewall will be configured to only allow traffic from Cloud Scheduler's known IP ranges, ensuring only the trusted GCP service can trigger the workflows.

## 4. Cost Analysis

This entire architecture is designed to fall within the GCP "Always Free" tier, resulting in **$0.00 per month** in operational costs.

| Resource | Free Tier Limit (Monthly) | Estimated Usage (Monthly) | Cost |
| :--- | :--- | :--- | :--- |
| **e2-micro VM** | 1 instance | 1 instance (730 hours) | $0 |
| **Standard Persistent Disk** | 30 GB | 10 GB | $0 |
| **Cloud Scheduler** | 3 jobs | 2 jobs (US, CN) | $0 |
| **IAP & VPC** | N/A (Free services) | N/A | $0 |
| **Egress Traffic** | 1 GB | < 100 MB | $0 |
| **Total** | | | **$0.00** |

This cost model is sustainable indefinitely, aligning perfectly with the project's "no burn-rate" financial constraint.
