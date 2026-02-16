"""Configuration models for Hyperliquid MCP Server."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ServerConfig(BaseModel):
    """Server information configuration."""

    name: str = "Hyperliquid MCP Server"
    version: str = "1.0.3"


class NetworkConfig(BaseModel):
    """Network settings for HTTP/SSE transports."""

    host: str = "localhost"
    port: int = Field(default=3000, ge=1, le=65535)


class TransportConfig(BaseModel):
    """Transport configuration."""

    type: Literal["stdio", "http", "sse"] = "stdio"
    network: NetworkConfig = Field(default_factory=NetworkConfig)


class Config(BaseModel):
    """Main configuration model."""

    server: ServerConfig = Field(default_factory=ServerConfig)
    transport: TransportConfig = Field(default_factory=TransportConfig)
