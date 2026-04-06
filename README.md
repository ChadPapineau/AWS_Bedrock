# Bedrock AgentCore Multi-Agent Swarm

A multi-agent system built on AWS Bedrock AgentCore using the Strands Agents SDK. Three specialized agents collaborate via the **Swarm orchestration pattern** to support AI & Secrets Management research, planning, and lab implementation.

## Architecture

```
                        +-------------------+
                        |    User Input     |
                        +--------+----------+
                                 |
                        +--------v----------+
                        |   Swarm Router    |
                        +--------+----------+
                                 |
              +------------------+------------------+
              |                  |                  |
     +--------v-------+ +-------v--------+ +-------v-----------+
     |  Scout Agent    | | Planner Agent  | | Lab Orchestrator  |
     |  (Research)     | | (Strategy)     | | (Implementation)  |
     +--------+-------+ +-------+--------+ +-------+-----------+
              |                  |                  |
     +--------v-------+ +-------v--------+ +-------v-----------+
     | web_search      | | file_read      | | python_repl       |
     | github_search   | | file_write     | | shell_exec        |
     | fetch_url       | |                | | architecture_rev  |
     +----------------+ +----------------+ | file_read/write   |
                                            +-------------------+
```

**Agent 1 -- Scout**: Scans the web and GitHub for relevant projects, emerging tech, security tooling, and industry trends. Entry point for research queries.

**Agent 2 -- Planner**: Translates research into contextualized plans for an AI & Secrets Management SME. Maintains a persistent knowledge base of decisions and lab context.

**Agent 3 -- Lab Orchestrator**: Provides architecture guidance, generates code scaffolds, runs shell commands, and produces structured architecture reviews.

Agents hand off to each other autonomously -- no central supervisor. The Scout finds, the Planner contextualizes, the Lab Orchestrator implements.

## Prerequisites

- Python 3.11+
- AWS account with Bedrock access (Claude models enabled)
- AWS CLI configured with appropriate credentials
- Node.js 18+ (for AgentCore CLI)
- Terraform 1.5+ (for infrastructure deployment)
- Docker (for container builds)

## Quick Start

### 1. Clone and Install

```bash
cd AWS_Bedrock
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys and AWS settings
```

Key variables:
| Variable | Description | Required |
|---|---|---|
| `AWS_REGION` | AWS region (default: us-east-1) | Yes |
| `BEDROCK_MODEL_ID` | Claude model ID | Yes |
| `TAVILY_API_KEY` | Tavily API key for web search | For Scout |
| `GITHUB_TOKEN` | GitHub PAT for repo search | For Scout |

### 3. Run Locally

```bash
# Install the AgentCore CLI
npm install -g @aws/agentcore-cli

# Start the local dev server with hot reload
agentcore dev

# In another terminal, invoke the swarm
agentcore invoke --dev '{"prompt": "Find the top 5 secrets management tools for Kubernetes"}'
```

### 4. Run Tests

```bash
pytest -v
```

## Deployment

### Build and Push Container

```bash
# Authenticate with ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account_id>.dkr.ecr.us-east-1.amazonaws.com

# Build and tag
docker build -t agentcore-swarm .
docker tag agentcore-swarm:latest <ecr_repo_url>:latest

# Push
docker push <ecr_repo_url>:latest
```

### Deploy Infrastructure

```bash
cd terraform
terraform init
terraform plan -var="environment=dev"
terraform apply -var="environment=dev"
```

### Deploy Runtime

After Terraform provisions the supporting infrastructure:

```bash
agentcore deploy
agentcore status
```

## Project Structure

```
src/
  main.py                  # AgentCore entrypoint + Swarm wiring
  agents/
    scout.py               # Agent 1: web/GitHub research
    planner.py             # Agent 2: strategic planning
    lab_orchestrator.py    # Agent 3: architecture & implementation
  tools/
    web_tools.py           # web_search, github_search, fetch_url
    file_tools.py          # file_read, file_write (knowledge base)
    lab_tools.py           # python_repl, shell_exec, architecture_review
  config/
    settings.py            # Centralized configuration via pydantic-settings
terraform/
  main.tf                  # Root module: ECR + submodules
  variables.tf             # Input variables
  outputs.tf               # Stack outputs
  modules/
    agentcore_runtime/     # Runtime IAM + CloudWatch
    agentcore_gateway/     # API Gateway + Lambda (MCP tool server)
    agentcore_memory/      # DynamoDB-backed session memory
    cognito/               # OAuth2 client credentials
    cyberark_scanner/      # CyberArk Secure AI Agents discovery scanner
tests/
  test_scout.py
  test_planner.py
  test_lab_orchestrator.py
```

## Example Workflows

**Research flow:**
> "What are the latest HashiCorp Vault alternatives for secrets management in Kubernetes?"
>
> Scout searches GitHub + web -> Planner maps findings to lab stack -> Lab Orchestrator proposes a PoC architecture

**Planning flow:**
> "Help me plan a migration from AWS Secrets Manager to Vault for our EKS clusters"
>
> Scout gathers migration guides -> Planner creates phased plan with risk assessment -> Lab Orchestrator generates Terraform + Helm scaffolds

**Implementation flow:**
> "Review my Vault HA architecture and suggest improvements"
>
> Lab Orchestrator produces a structured architecture review -> hands to Scout for best-practice validation -> Planner records decisions to knowledge base

## CyberArk Secure AI Agents Integration

The agent swarm integrates with [CyberArk Secure AI Agents](https://docs.cyberark.com/early-release/secure-ai-agents/content/secureai/discoveryaws.htm) for continuous discovery, risk analysis, and remediation of the deployed agents.

```
+---------------------------+          +------------------------------+
|       AWS Account         |          |     CyberArk Tenant          |
|                           |          |                              |
|  AgentCore Runtime        |          |  Identity Administration     |
|  +-----+ +-----+ +-----+ |          |    (service user + role)     |
|  |Scout| |Plan | |Lab  | |          |                              |
|  +-----+ +-----+ +-----+ |  reports |  Discovery & Context         |
|                           +--------->+    (inventory + risk dash)   |
|  CyberArk Scanner         |          |                              |
|  (Glue ETL every 12hrs)  |          |  Secure AI Agents            |
|  S3 | Secrets Mgr | IAM  |          |    (remediation actions)     |
+---------------------------+          +------------------------------+
```

### Prerequisites

1. CyberArk Identity tenant with **Secure AI Agents** entitlement
2. Download the [AWS Bedrock scanner](https://community.cyberark.com/marketplace/s/#software-aK4Vy00000001FRKAY-) from the CyberArk Marketplace

### Setup

#### Step 1: Create CyberArk Identity Service User

In CyberArk Identity Administration:
1. Go to **Core Services > Users**
2. Click **Add User** -- set it as an OAuth confidential client + service user
3. Name it meaningfully (e.g., your AWS account ID)
4. Go to **Core Services > Roles**, find **Discovery & Context AWS Communication**
5. Add the service user to this role

#### Step 2: Deploy the Scanner via Terraform

```bash
cd terraform

# Create a tfvars file with your CyberArk config
cat > cyberark.auto.tfvars <<EOF
enable_cyberark_scanner     = true
cyberark_tenant_name        = "your-tenant-name"
cyberark_service_user       = "scanner-service-user"
cyberark_service_password   = "your-service-password"
cyberark_scanner_artifacts_path = "/path/to/downloaded/scanner"
EOF

terraform plan
terraform apply
```

The module deploys:
| Resource | Purpose |
|---|---|
| S3 Bucket | Stores `discovery.py` and `dependencies.zip` |
| Secrets Manager | Securely stores CyberArk service user credentials |
| Glue ETL Job | Runs discovery using `bedrock:Get*`, `bedrock-agentcore:List*` |
| Glue Trigger | Scheduled scan every 12 hours + on-demand trigger |
| IAM Role | Least-privilege access for the scanner |

#### Step 3: Trigger Initial Scan

```bash
# Run the scanner immediately
aws glue start-job-run --job-name $(terraform output -raw cyberark_scanner_job_name)
```

#### Step 4: Verify in CyberArk Dashboard

1. Log in to your CyberArk tenant
2. Open **Discovery & Context > AI Agents**
3. Your Scout, Planner, and Lab Orchestrator agents should appear in the inventory
4. Review risk analysis and apply any recommended remediation actions

### What the Scanner Discovers

The scanner inventories each agent with:
- Agent name, type, and description
- Foundation model in use
- Creation/update timestamps
- Connection status
- Action groups and versions
- Owner assignment status

Discovery & Context then computes risk scores based on:
- **Missing owner** -- no accountability for security updates
- **Pending connection** -- stale agents with potentially unused secrets
- **Excessive permissions** -- overly broad IAM policies

### Uninstall

```bash
# Remove scanner resources
terraform destroy -target=module.cyberark_scanner

# Or delete the CloudFormation stack directly
aws cloudformation delete-stack --stack-name cyberark-discovery --region us-east-1
```

## Configuration

Per-agent model overrides are supported via environment variables:

```bash
SCOUT_MODEL_ID=us.anthropic.claude-3-5-sonnet-20241022-v2:0
PLANNER_MODEL_ID=us.anthropic.claude-3-5-sonnet-20241022-v2:0
LAB_MODEL_ID=us.anthropic.claude-3-5-sonnet-20241022-v2:0
```

Temperature defaults are tuned per agent role (Scout: 0.6, Planner: 0.5, Lab Orchestrator: 0.7).
