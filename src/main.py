"""Bedrock AgentCore entrypoint -- Multi-Agent Swarm.

Wires the Scout, Planner, and Lab Orchestrator agents into a Strands Swarm
and exposes them via the BedrockAgentCoreApp runtime interface.

The Swarm pattern allows agents to autonomously hand off tasks to one another
without a central supervisor. The Scout serves as the default entry point.
"""

from __future__ import annotations

import logging
import sys

from bedrock_agentcore import BedrockAgentCoreApp
from strands.multiagent import Swarm

from src.agents import (
    create_lab_orchestrator_agent,
    create_planner_agent,
    create_scout_agent,
)
from src.config import settings

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)


def build_swarm() -> Swarm:
    """Construct the 3-agent swarm with cross-agent handoff wiring."""
    logger.info("Initializing agents...")

    scout = create_scout_agent()
    planner = create_planner_agent()
    lab_orchestrator = create_lab_orchestrator_agent()

    logger.info(
        "Building swarm: Scout (entry) -> Planner -> Lab Orchestrator "
        "(with bidirectional handoffs)"
    )

    swarm = Swarm(
        agents=[scout, planner, lab_orchestrator],
        entry_point=scout,
        max_handoffs=15,
        max_iterations=20,
    )

    return swarm


app = BedrockAgentCoreApp()
swarm = build_swarm()


@app.entrypoint
async def handler(request: dict):
    """Handle incoming requests by routing them through the agent swarm.

    The swarm automatically determines which agent should handle the request
    based on content analysis and agent system prompts.
    """
    prompt = request.get("prompt", "")
    if not prompt:
        yield {"error": "No prompt provided in request"}
        return

    logger.info("Received prompt (%d chars), routing through swarm...", len(prompt))

    async for event in swarm.stream_async(prompt):
        yield event


def main():
    """Run the AgentCore application."""
    logger.info("Starting Bedrock AgentCore Swarm...")
    logger.info("Model: %s | Region: %s", settings.bedrock_model_id, settings.aws_region)
    app.run()


if __name__ == "__main__":
    main()
