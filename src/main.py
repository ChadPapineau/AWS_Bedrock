"""Bedrock AgentCore entrypoint -- Multi-Agent Swarm.

Wires the Scout, Planner, and Lab Orchestrator agents into a Strands Swarm
and exposes them via the BedrockAgentCoreApp runtime interface.

The Swarm pattern allows agents to autonomously hand off tasks to one another
without a central supervisor. The Scout serves as the default entry point.
"""

from __future__ import annotations

import logging
import sys
import traceback

from bedrock_agentcore import BedrockAgentCoreApp

from src.config import settings

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

app = BedrockAgentCoreApp()

_swarm = None
_swarm_error = None


def _get_swarm():
    """Lazy-initialize the swarm on first request.

    This keeps the server responsive to /ping health checks even if agent
    initialization fails, ensuring errors reach CloudWatch instead of
    silently crashing the container.
    """
    global _swarm, _swarm_error

    if _swarm is not None:
        return _swarm
    if _swarm_error is not None:
        raise _swarm_error

    try:
        from strands.multiagent import Swarm

        from src.agents import (
            create_lab_orchestrator_agent,
            create_planner_agent,
            create_scout_agent,
        )

        logger.info("Initializing agents...")
        scout = create_scout_agent()
        planner = create_planner_agent()
        lab_orchestrator = create_lab_orchestrator_agent()

        logger.info(
            "Building swarm: Scout (entry) -> Planner -> Lab Orchestrator "
            "(with bidirectional handoffs)"
        )

        _swarm = Swarm(
            nodes=[scout, planner, lab_orchestrator],
            entry_point=scout,
            max_handoffs=15,
            max_iterations=20,
        )
        logger.info("Swarm initialized successfully")
        return _swarm
    except Exception as exc:
        logger.exception("Failed to initialize swarm")
        _swarm_error = exc
        raise


@app.entrypoint
async def handler(request: dict):
    """Handle incoming requests by routing them through the agent swarm."""
    prompt = request.get("prompt", "")
    if not prompt:
        yield {"error": "No prompt provided in request"}
        return

    logger.info("Received prompt (%d chars), routing through swarm...", len(prompt))

    try:
        swarm = _get_swarm()
    except Exception as exc:
        logger.exception("Swarm unavailable")
        yield {"error": f"Swarm initialization failed: {exc}"}
        return

    async for event in swarm.stream_async(prompt):
        yield event


def main():
    """Run the AgentCore application."""
    logger.info("Starting Bedrock AgentCore Swarm...")
    logger.info("Model: %s | Region: %s", settings.bedrock_model_id, settings.aws_region)
    try:
        app.run()
    except Exception:
        logger.exception("Application crashed")
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        raise


if __name__ == "__main__":
    main()
