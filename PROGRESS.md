# Bedrock AgentCore Multi-Agent Swarm — Progress Summary

## 1. Planning & Design

- Designed a 3-agent multi-agent system for an AI & Secrets Management SME:
  - **Scout** — research & discovery
  - **Planner** — strategy & context
  - **Lab Orchestrator** — architecture & implementation
- Selected the tech stack:
  - **Strands Agents SDK** (Python)
  - **Swarm orchestration pattern** — autonomous handoffs, no central supervisor
  - **Terraform** for infrastructure-as-code
  - **Claude Sonnet 4.6** on **Amazon Bedrock** via cross-region inference profile

## 2. Code Scaffold (29 files)

- `src/agents/` — Three agent modules with detailed system prompts, tool bindings, and named identities for proper swarm handoffs.
- `src/tools/` — Custom tool implementations:
  - `web_tools` — Tavily search, GitHub search, URL fetch
  - `file_tools` — Read/write with path traversal prevention
  - `lab_tools` — Python REPL, allowlisted shell commands, architecture review
- `src/config/settings.py` — Pydantic-based settings with per-agent model overrides, loaded from environment variables.
- `src/main.py` — AgentCore entrypoint that lazy-initializes the Swarm and exposes it via `BedrockAgentCoreApp` with streaming SSE responses.
- `Dockerfile` — arm64 container image based on Python 3.11-slim.
- `tests/` — Unit tests for all tool modules.

## 3. Terraform Infrastructure (7 modules)

| Module | Purpose |
|--------|---------|
| **ECR** | Container registry for the agent Docker image |
| **Cognito** | User pool with OAuth2 client credentials for agent authentication |
| **AgentCore Memory** | DynamoDB-backed persistent memory |
| **AgentCore Gateway** | Lambda + API Gateway v2 for MCP tool endpoints |
| **AgentCore Runtime** | IAM role, CloudWatch log group, Bedrock invoke permissions across all regions and inference profiles |
| **CyberArk Scanner** *(optional)* | S3 bucket, Secrets Manager, Glue ETL job, and triggers for CyberArk Secure AI Agents discovery |

All modules deployed via `terraform apply` in `ca-central-1`.

## 4. GitHub Repository

- Initialized git repository.
- Pushed to a **private GitHub repo**.
- Added `ZAG23` as a collaborator.

## 5. AWS Deployment & Debugging

- Configured AWS credentials (IAM user `Chad-Bedrock` with a comprehensive custom policy).
- Built the Docker image for `linux/arm64`, pushed to ECR.
- Created the AgentCore Runtime (`agentcoreSwarmDev`) and a default endpoint via the AWS CLI control plane.

### Issues Resolved

| Issue | Root Cause | Fix |
|-------|-----------|-----|
| Swarm constructor error | `agents=` parameter renamed to `nodes=` in SDK | Updated `src/main.py` |
| Silent container crash (no CloudWatch logs) | Swarm initialized at module import time; any failure killed the container before logs could be written | Made initialization lazy — deferred to first request |
| Handoffs failing | Agents had no `name`; auto-assigned `node_0`, `node_1`, `node_2` didn't match system prompt references | Added explicit `name` and `description` to each agent |
| `ValidationException` on model ID | `anthropic.claude-sonnet-4-6` requires a cross-region inference profile in `ca-central-1` | Changed to `us.anthropic.claude-sonnet-4-6` |
| `AccessDeniedException` on Bedrock invoke | IAM policy only covered `foundation-model/*` in `ca-central-1`; inference profiles route across regions | Wildcarded region and added `inference-profile/*` resources |
| `ValidationException` on model parameters | Claude Sonnet 4.6 doesn't allow both `temperature` and `top_p` | Removed `top_p` from model config |

## 6. Verified Working

- Invoked the swarm with a test prompt.
- The **Scout Agent** responded in **3.6 seconds** (1,782 tokens).
- Correctly identified itself, listed the **Planner** and **Lab Orchestrator** by name with descriptions, and confirmed the swarm is fully operational.
- Final status: **COMPLETED** — runtime version 5.

---

**Deployment:** Live on **AWS Bedrock AgentCore** in `ca-central-1`, running Claude Sonnet 4.6 via cross-region inference, with all three agents ready to handle research, planning, and implementation tasks through autonomous handoffs.
