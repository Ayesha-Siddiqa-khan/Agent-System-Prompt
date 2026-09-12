"""Production-grade, cloud-native FastAPI microservice optimized for Kubernetes."""

import logging
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Response, status
from prometheus_fastapi_instrumentator import Instrumentator

from src.app.config import Settings, get_settings

# Configure structured production logging
settings: Settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format='{"time":"%(asctime)s","level":"%(levelname)s","name":"%(name)s","message":"%(message)s"}',
    stream=sys.stdout,
)
logger = logging.getLogger(settings.SERVICE_NAME)

# State variable for Kubernetes readiness probe
app_state: dict[str, Any] = {"is_ready": False}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application startup and graceful shutdown lifecycle."""
    logger.info(
        "Starting up %s in %s environment (v%s)...",
        settings.SERVICE_NAME,
        settings.ENVIRONMENT,
        settings.VERSION,
    )
    # Perform startup tasks (e.g., establish connection pools, warmup)
    app_state["is_ready"] = True
    logger.info("Application is ready to receive traffic on port %d", settings.PORT)

    yield

    # Perform graceful shutdown cleanup (e.g., drain queues, close connections)
    logger.info("Graceful shutdown initiated. Marking readiness as False...")
    app_state["is_ready"] = False
    logger.info("Shutdown complete.")


app = FastAPI(
    title=settings.SERVICE_NAME,
    version=settings.VERSION,
    description="Production-grade cloud-native microservice optimized for Kubernetes.",
    lifespan=lifespan,
)

# Setup Prometheus metrics instrumentation
instrumentator = Instrumentator(
    should_group_status_codes=False,
    excluded_handlers=["/metrics", "/healthz", "/ready"],
)
instrumentator.instrument(app).expose(app, endpoint="/metrics", tags=["Monitoring"])


@app.get(
    "/",
    tags=["General"],
    summary="Root Service Metadata",
    response_description="Basic metadata about service name, status, and environment",
)
async def root() -> dict[str, str]:
    """Root endpoint returning service identity, operational status, and environment."""
    return {
        "service": settings.SERVICE_NAME,
        "status": "running",
        "environment": settings.ENVIRONMENT,
        "version": settings.VERSION,
    }


@app.get(
    "/healthz",
    tags=["Probes"],
    summary="Kubernetes Liveness Probe",
    response_description="Confirms that the service process is alive",
    status_code=status.HTTP_200_OK,
)
async def liveness() -> dict[str, str]:
    """Liveness probe to ensure the container runtime process is running and not deadlocked."""
    return {"status": "alive"}


@app.get(
    "/ready",
    tags=["Probes"],
    summary="Kubernetes Readiness Probe",
    response_description="Confirms whether the service is ready to handle external traffic",
)
async def readiness(response: Response) -> dict[str, str]:
    """Readiness probe checking if dependencies and initialization state are ready to serve."""
    if not app_state.get("is_ready", False):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not_ready"}
    return {"status": "ready"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower(),
        reload=False,
    )
