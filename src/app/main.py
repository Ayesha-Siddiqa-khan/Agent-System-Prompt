"""Production-grade, cloud-native FastAPI microservice optimized for Kubernetes."""

import logging
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, Response, status
from fastapi.responses import HTMLResponse, JSONResponse
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
    docs_url=None,
    redoc_url=None,
)

SCALAR_HTML_TEMPLATE = """<!doctype html>
<html lang="en">
  <head>
    <title>__SERVICE_NAME__ - API Reference</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
      :root {
        --scalar-font: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        --scalar-font-code: 'JetBrains Mono', monospace;
      }

      body {
        margin: 0;
        padding: 0;
        background: #070a13;
        color: #f8fafc;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        position: relative;
        overflow-x: hidden;
      }

      /* Ambient glowing neon backdrop */
      body::before {
        content: '';
        position: fixed;
        top: -160px;
        left: 20%;
        width: 650px;
        height: 650px;
        background: radial-gradient(circle, rgba(99, 102, 241, 0.28) 0%, rgba(168, 85, 247, 0.18) 45%, transparent 70%);
        filter: blur(120px);
        pointer-events: none;
        z-index: 0;
      }

      body::after {
        content: '';
        position: fixed;
        bottom: -160px;
        right: 15%;
        width: 600px;
        height: 600px;
        background: radial-gradient(circle, rgba(6, 182, 212, 0.25) 0%, rgba(59, 130, 246, 0.18) 50%, transparent 70%);
        filter: blur(120px);
        pointer-events: none;
        z-index: 0;
      }
    </style>
  </head>
  <body>
    <div id="app"></div>
    <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
    <script>
      const scalarCustomStyles = `
        :root, .dark-mode {
          --scalar-color-accent: #818cf8 !important;
          --scalar-background-1: #070a13 !important;
          --scalar-background-2: #0e1424 !important;
          --scalar-background-3: #141d33 !important;
          --scalar-background-accent: rgba(99, 102, 241, 0.18) !important;
          --scalar-border-color: rgba(255, 255, 255, 0.08) !important;
        }

        .scalar-api-reference {
          background: transparent !important;
        }

        /* Beautiful glowing header with gradient title */
        .section-header h1, h1, .scalar-card-title {
          background: linear-gradient(135deg, #ffffff 15%, #a5b4fc 55%, #38bdf8 100%) !important;
          -webkit-background-clip: text !important;
          -webkit-text-fill-color: transparent !important;
          font-weight: 800 !important;
          letter-spacing: -0.02em !important;
        }

        /* Gradient glowing cards with glassmorphism */
        .scalar-card, .card, .client-libraries, .scalar-card-content {
          background: rgba(14, 20, 36, 0.75) !important;
          border: 1px solid rgba(99, 102, 241, 0.25) !important;
          border-radius: 16px !important;
          backdrop-filter: blur(24px) !important;
          -webkit-backdrop-filter: blur(24px) !important;
          box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5) !important;
        }

        /* Gradient radiant action buttons */
        button.scalar-button, button[type="submit"], .scalar-card-footer button, .test-request-button, .show-more-button {
          background: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #06b6d4 100%) !important;
          color: #ffffff !important;
          border: none !important;
          border-radius: 10px !important;
          font-weight: 600 !important;
          box-shadow: 0 4px 20px rgba(99, 102, 241, 0.45) !important;
          transition: all 0.25s ease !important;
        }

        button.scalar-button:hover, button[type="submit"]:hover {
          transform: translateY(-2px) !important;
          box-shadow: 0 8px 28px rgba(99, 102, 241, 0.65) !important;
        }

        /* Sidebar glowing border & active item styling */
        .sidebar {
          background: rgba(7, 10, 19, 0.7) !important;
          border-right: 1px solid rgba(99, 102, 241, 0.2) !important;
          backdrop-filter: blur(20px) !important;
        }

        .sidebar-item-active, .sidebar-heading-active {
          background: linear-gradient(90deg, rgba(99, 102, 241, 0.25) 0%, rgba(6, 182, 212, 0.08) 100%) !important;
          border-left: 3px solid #818cf8 !important;
          color: #38bdf8 !important;
          font-weight: 700 !important;
        }

        /* Endpoint badges with vibrant glowing neon pill */
        .badge, [class*="badge-"] {
          border-radius: 9999px !important;
          font-weight: 700 !important;
          text-transform: uppercase !important;
          letter-spacing: 0.05em !important;
        }

        .badge-get, .method-get {
          background: linear-gradient(135deg, rgba(99, 102, 241, 0.25), rgba(6, 182, 212, 0.25)) !important;
          border: 1px solid rgba(56, 189, 248, 0.5) !important;
          color: #38bdf8 !important;
          box-shadow: 0 0 12px rgba(56, 189, 248, 0.2) !important;
        }
      `;

      Scalar.createApiReference('#app', {
        url: '/openapi.json',
        theme: 'deepSpace',
        layout: 'modern',
        showSidebar: true,
        darkMode: true,
        hideDarkModeToggle: false,
        searchHotKey: 'k',
        customCss: scalarCustomStyles,
      })
    </script>
  </body>
</html>"""

@app.get("/docs", include_in_schema=False)
async def custom_scalar_docs_html():
    """Render state-of-the-art Scalar API reference documentation with beautiful glowing gradients."""
    html = SCALAR_HTML_TEMPLATE.replace("__SERVICE_NAME__", settings.SERVICE_NAME)
    return HTMLResponse(content=html)

# Setup Prometheus metrics instrumentation
instrumentator = Instrumentator(
    should_group_status_codes=False,
    excluded_handlers=["/metrics", "/healthz", "/ready"],
)
instrumentator.instrument(app).expose(app, endpoint="/metrics", tags=["Monitoring"])

LANDING_PAGE_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Agent System Prompt | Cloud-Native Platform</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-dark: #090d16;
      --card-bg: rgba(18, 24, 38, 0.7);
      --card-border: rgba(255, 255, 255, 0.08);
      --primary: #6366f1;
      --primary-glow: rgba(99, 102, 241, 0.4);
      --secondary: #06b6d4;
      --accent: #10b981;
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --font-sans: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
      --font-mono: 'JetBrains Mono', monospace;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      background-color: var(--bg-dark);
      color: var(--text-main);
      font-family: var(--font-sans);
      min-height: 100vh;
      overflow-x: hidden;
      position: relative;
    }

    /* Ambient glowing background gradients */
    .ambient-glow-1 {
      position: absolute;
      top: -120px;
      left: 10%;
      width: 500px;
      height: 500px;
      background: radial-gradient(circle, rgba(99, 102, 241, 0.25) 0%, transparent 70%);
      filter: blur(80px);
      z-index: 0;
      pointer-events: none;
    }

    .ambient-glow-2 {
      position: absolute;
      top: 200px;
      right: 5%;
      width: 450px;
      height: 450px;
      background: radial-gradient(circle, rgba(6, 182, 212, 0.2) 0%, transparent 70%);
      filter: blur(90px);
      z-index: 0;
      pointer-events: none;
    }

    .container {
      max-width: 1200px;
      margin: 0 auto;
      padding: 40px 24px 80px 24px;
      position: relative;
      z-index: 1;
    }

    /* Navbar */
    .navbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16px 24px;
      background: rgba(18, 24, 38, 0.6);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border: 1px solid var(--card-border);
      border-radius: 20px;
      margin-bottom: 48px;
    }

    .nav-brand {
      display: flex;
      align-items: center;
      gap: 12px;
      font-weight: 700;
      font-size: 1.15rem;
      letter-spacing: -0.02em;
    }

    .logo-badge {
      width: 36px;
      height: 36px;
      border-radius: 10px;
      background: linear-gradient(135deg, var(--primary), var(--secondary));
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 4px 14px var(--primary-glow);
    }

    .status-pill {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      background: rgba(16, 185, 129, 0.12);
      border: 1px solid rgba(16, 185, 129, 0.3);
      color: #34d399;
      font-size: 0.85rem;
      font-weight: 600;
      padding: 6px 14px;
      border-radius: 9999px;
    }

    .status-dot {
      width: 8px;
      height: 8px;
      background-color: #10b981;
      border-radius: 50%;
      box-shadow: 0 0 10px #10b981;
      animation: pulse 2s infinite;
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.4; transform: scale(1.15); }
    }

    /* Hero section */
    .hero {
      text-align: center;
      max-width: 800px;
      margin: 0 auto 56px auto;
    }

    .hero-badge {
      display: inline-block;
      padding: 6px 16px;
      border-radius: 9999px;
      background: rgba(99, 102, 241, 0.12);
      border: 1px solid rgba(99, 102, 241, 0.3);
      color: #a5b4fc;
      font-size: 0.825rem;
      font-weight: 600;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      margin-bottom: 20px;
    }

    .hero h1 {
      font-size: 3.25rem;
      font-weight: 800;
      line-height: 1.15;
      letter-spacing: -0.03em;
      margin-bottom: 20px;
      background: linear-gradient(180deg, #ffffff 30%, #94a3b8 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .hero p {
      font-size: 1.15rem;
      color: var(--text-muted);
      line-height: 1.6;
      margin-bottom: 32px;
    }

    .hero-actions {
      display: flex;
      justify-content: center;
      gap: 16px;
      flex-wrap: wrap;
    }

    .btn {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 12px 26px;
      border-radius: 12px;
      font-weight: 600;
      font-size: 0.95rem;
      text-decoration: none;
      transition: all 0.25s ease;
      cursor: pointer;
    }

    .btn-primary {
      background: linear-gradient(135deg, var(--primary), #4f46e5);
      color: #fff;
      box-shadow: 0 4px 20px var(--primary-glow);
      border: 1px solid rgba(255, 255, 255, 0.15);
    }

    .btn-primary:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(99, 102, 241, 0.5);
    }

    .btn-secondary {
      background: rgba(255, 255, 255, 0.05);
      color: var(--text-main);
      border: 1px solid var(--card-border);
      backdrop-filter: blur(8px);
    }

    .btn-secondary:hover {
      background: rgba(255, 255, 255, 0.1);
      transform: translateY(-2px);
    }

    /* Cards Grid */
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 24px;
      margin-bottom: 48px;
    }

    .card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 20px;
      padding: 28px;
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      transition: transform 0.3s ease, border-color 0.3s ease;
      position: relative;
      overflow: hidden;
    }

    .card:hover {
      transform: translateY(-4px);
      border-color: rgba(99, 102, 241, 0.4);
    }

    .card-icon {
      width: 44px;
      height: 44px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-bottom: 18px;
    }

    .card-icon.blue { background: rgba(99, 102, 241, 0.15); color: #818cf8; }
    .card-icon.cyan { background: rgba(6, 182, 212, 0.15); color: #22d3ee; }
    .card-icon.emerald { background: rgba(16, 185, 129, 0.15); color: #34d399; }

    .card h3 {
      font-size: 1.25rem;
      font-weight: 700;
      margin-bottom: 10px;
      letter-spacing: -0.01em;
    }

    .card p {
      color: var(--text-muted);
      font-size: 0.925rem;
      line-height: 1.5;
      margin-bottom: 20px;
    }

    .spec-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.85rem;
    }

    .spec-table tr {
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }

    .spec-table tr:last-child {
      border-bottom: none;
    }

    .spec-table td {
      padding: 8px 0;
    }

    .spec-label {
      color: var(--text-muted);
    }

    .spec-value {
      font-family: var(--font-mono);
      font-weight: 500;
      color: #e2e8f0;
      text-align: right;
    }

    /* Interactive live tester */
    .terminal-card {
      background: #0d1117;
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 20px;
      padding: 24px;
      margin-bottom: 48px;
    }

    .terminal-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 16px;
      padding-bottom: 12px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }

    .dots {
      display: flex;
      gap: 6px;
    }

    .dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
    }

    .dot.red { background: #ef4444; }
    .dot.yellow { background: #f59e0b; }
    .dot.green { background: #10b981; }

    .terminal-title {
      font-family: var(--font-mono);
      font-size: 0.8rem;
      color: var(--text-muted);
    }

    .tester-controls {
      display: flex;
      gap: 12px;
      margin-bottom: 16px;
      flex-wrap: wrap;
    }

    .test-pill {
      background: rgba(255, 255, 255, 0.06);
      border: 1px solid rgba(255, 255, 255, 0.1);
      color: var(--text-main);
      padding: 8px 16px;
      border-radius: 8px;
      font-family: var(--font-mono);
      font-size: 0.85rem;
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .test-pill:hover, .test-pill.active {
      background: var(--primary);
      border-color: var(--primary);
      color: #fff;
    }

    pre.output {
      background: #050811;
      padding: 16px;
      border-radius: 12px;
      font-family: var(--font-mono);
      font-size: 0.875rem;
      color: #38bdf8;
      overflow-x: auto;
      border: 1px solid rgba(255, 255, 255, 0.05);
      min-height: 70px;
    }

    /* Footer */
    footer {
      text-align: center;
      color: var(--text-muted);
      font-size: 0.85rem;
      padding-top: 32px;
      border-top: 1px solid var(--card-border);
    }

    @media (max-width: 768px) {
      .hero h1 { font-size: 2.25rem; }
      .navbar { flex-direction: column; gap: 16px; align-items: flex-start; }
    }
  </style>
</head>
<body>
  <div class="ambient-glow-1"></div>
  <div class="ambient-glow-2"></div>

  <div class="container">
    <!-- Navigation Bar -->
    <nav class="navbar">
      <div class="nav-brand">
        <div class="logo-badge">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
          </svg>
        </div>
        <span>Agent System Prompt</span>
      </div>
      <div class="status-pill">
        <span class="status-dot"></span>
        <span>Kubernetes Cluster Active</span>
      </div>
    </nav>

    <!-- Hero Section -->
    <section class="hero">
      <div class="hero-badge">Production Kubernetes Environment</div>
      <h1>Cloud-Native Microservice Architecture</h1>
      <p>High-performance FastAPI service running on a multi-node Kubernetes cluster deployed via Terraform on AWS EC2 with automated GitHub Actions CI/CD pipelines.</p>
      <div class="hero-actions">
        <a href="/docs" class="btn btn-primary">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
          Open Swagger UI Docs
        </a>
        <a href="/metrics" class="btn btn-secondary" target="_blank">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 20V10"></path><path d="M12 20V4"></path><path d="M6 20v-6"></path></svg>
          Prometheus Metrics
        </a>
      </div>
    </section>

    <!-- Architecture & Health Grid -->
    <div class="grid">
      <div class="card">
        <div class="card-icon blue">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>
        </div>
        <h3>Service Overview</h3>
        <p>Operational metadata and runtime versioning for this container deployment.</p>
        <table class="spec-table">
          <tr><td class="spec-label">Service</td><td class="spec-value">cloud-native-service</td></tr>
          <tr><td class="spec-label">Environment</td><td class="spec-value">production</td></tr>
          <tr><td class="spec-label">Version</td><td class="spec-value">v1.0.0</td></tr>
          <tr><td class="spec-label">Runtime</td><td class="spec-value">Python 3.11 / Uvicorn</td></tr>
        </table>
      </div>

      <div class="card">
        <div class="card-icon cyan">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>
        </div>
        <h3>Kubernetes Topology</h3>
        <p>Self-managed cluster joined with Calico CNI networking & container orchestration.</p>
        <table class="spec-table">
          <tr><td class="spec-label">Control Plane</td><td class="spec-value">10.0.1.121 (Master)</td></tr>
          <tr><td class="spec-label">Worker Node</td><td class="spec-value">10.0.1.164 (Ready)</td></tr>
          <tr><td class="spec-label">Container Engine</td><td class="spec-value">containerd://2.2.1</td></tr>
          <tr><td class="spec-label">K8s Version</td><td class="spec-value">v1.30.14</td></tr>
        </table>
      </div>

      <div class="card">
        <div class="card-icon emerald">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"></path></svg>
        </div>
        <h3>Automated CI/CD</h3>
        <p>Continuous integration via GitHub Actions with zero-static-secrets AWS OIDC.</p>
        <table class="spec-table">
          <tr><td class="spec-label">Registry</td><td class="spec-value">AWS ECR us-east-1</td></tr>
          <tr><td class="spec-label">Auth Method</td><td class="spec-value">OIDC Web Identity</td></tr>
          <tr><td class="spec-label">Reverse Proxy</td><td class="spec-value">Nginx 1.24</td></tr>
          <tr><td class="spec-label">Liveness Probe</td><td class="spec-value">HTTP 200 OK</td></tr>
        </table>
      </div>
    </div>

    <!-- Live Endpoint Interactive Console -->
    <div class="terminal-card">
      <div class="terminal-header">
        <div class="dots">
          <div class="dot red"></div>
          <div class="dot yellow"></div>
          <div class="dot green"></div>
        </div>
        <div class="terminal-title">LIVE API CONSOLE // CLICK TO TEST ENDPOINTS</div>
        <div></div>
      </div>
      <div class="tester-controls">
        <button class="test-pill active" onclick="callApi('/healthz', this)">GET /healthz</button>
        <button class="test-pill" onclick="callApi('/ready', this)">GET /ready</button>
        <button class="test-pill" onclick="callApi('/?format=json', this)">GET / (JSON)</button>
        <button class="test-pill" onclick="window.open('/docs', '_blank')">↗ /docs (Swagger)</button>
      </div>
      <pre id="api-output" class="output">Click an endpoint above to execute a real-time probe test...</pre>
    </div>

    <footer>
      &copy; 2026 Agent System Prompt Platform &bull; Deployed on AWS via TerraPilot &bull; All Systems Operational
    </footer>
  </div>

  <script>
    async function callApi(path, element) {
      document.querySelectorAll('.test-pill').forEach(btn => btn.classList.remove('active'));
      if (element) element.classList.add('active');
      const output = document.getElementById('api-output');
      output.innerText = 'Calling ' + path + '...';
      try {
        const res = await fetch(path, { headers: { 'Accept': 'application/json' } });
        const data = await res.json();
        output.innerText = JSON.stringify(data, null, 2);
      } catch (err) {
        output.innerText = 'Error: ' + err.message;
      }
    }
    // Auto-run first probe
    window.addEventListener('DOMContentLoaded', () => callApi('/healthz'));
  </script>
</body>
</html>
"""


@app.get(
    "/",
    tags=["General"],
    summary="Root Service Metadata & Dashboard",
    response_description="Interactive landing page or service metadata JSON",
)
async def root(request: Request) -> Any:
    """Return an interactive modern dashboard for browsers, or JSON metadata for API clients."""
    accept = request.headers.get("accept", "")
    format_param = request.query_params.get("format", "")

    # If requested by a web browser, return the responsive dashboard
    if "text/html" in accept and format_param != "json":
        return HTMLResponse(content=LANDING_PAGE_HTML, status_code=status.HTTP_200_OK)

    # Otherwise return JSON metadata
    return JSONResponse(
        content={
            "service": settings.SERVICE_NAME,
            "status": "running",
            "environment": settings.ENVIRONMENT,
            "version": settings.VERSION,
        }
    )


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
