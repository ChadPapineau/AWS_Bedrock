from __future__ import annotations

import os
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class BedrockModelConfig(BaseSettings):
    """Per-agent model configuration with sensible defaults."""

    model_id: str = Field(default="us.anthropic.claude-3-5-sonnet-20241022-v2:0")
    max_tokens: int = Field(default=4096)
    temperature: float = Field(default=0.7)
    top_p: float = Field(default=0.9)


class Settings(BaseSettings):
    """Application-wide settings loaded from environment variables and .env files."""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    # AWS
    aws_region: str = Field(default="us-east-1", alias="AWS_REGION")
    aws_profile: str | None = Field(default=None, alias="AWS_PROFILE")

    # Bedrock defaults
    bedrock_model_id: str = Field(
        default="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        alias="BEDROCK_MODEL_ID",
    )
    bedrock_max_tokens: int = Field(default=4096, alias="BEDROCK_MAX_TOKENS")

    # AgentCore
    agentcore_memory_id: str | None = Field(default=None, alias="AGENTCORE_MEMORY_ID")
    agentcore_runtime_endpoint: str | None = Field(default=None, alias="AGENTCORE_RUNTIME_ENDPOINT")

    # Tool API keys
    tavily_api_key: str | None = Field(default=None, alias="TAVILY_API_KEY")
    github_token: str | None = Field(default=None, alias="GITHUB_TOKEN")

    # CyberArk Secure AI Agents
    cyberark_tenant_name: str | None = Field(default=None, alias="CYBERARK_TENANT_NAME")
    cyberark_scanner_bucket: str | None = Field(default=None, alias="CYBERARK_SCANNER_BUCKET")
    cyberark_scanner_region: str | None = Field(default=None, alias="CYBERARK_SCANNER_REGION")

    # Runtime flags
    local_dev: bool = Field(default=False, alias="LOCAL_DEV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # --- Per-agent model overrides ---

    @property
    def scout_model(self) -> BedrockModelConfig:
        return BedrockModelConfig(
            model_id=os.getenv("SCOUT_MODEL_ID", self.bedrock_model_id),
            max_tokens=int(os.getenv("SCOUT_MAX_TOKENS", str(self.bedrock_max_tokens))),
            temperature=0.6,
        )

    @property
    def planner_model(self) -> BedrockModelConfig:
        return BedrockModelConfig(
            model_id=os.getenv("PLANNER_MODEL_ID", self.bedrock_model_id),
            max_tokens=int(os.getenv("PLANNER_MAX_TOKENS", str(self.bedrock_max_tokens))),
            temperature=0.5,
        )

    @property
    def lab_orchestrator_model(self) -> BedrockModelConfig:
        return BedrockModelConfig(
            model_id=os.getenv("LAB_MODEL_ID", self.bedrock_model_id),
            max_tokens=int(os.getenv("LAB_MAX_TOKENS", str(self.bedrock_max_tokens))),
            temperature=0.7,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
