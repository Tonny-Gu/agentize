# syntax=docker/dockerfile:1

# =============================================================================
# Agentize Development Sandbox
# =============================================================================
# A comprehensive development environment container for agentize SDK development
# =============================================================================

# -----------------------------------------------------------------------------
# Arguments
# -----------------------------------------------------------------------------
ARG HOST_ARCH=amd64

# -----------------------------------------------------------------------------
# Stage 1: System Base
# -----------------------------------------------------------------------------
FROM ubuntu:24.04 AS system-base

ENV DEBIAN_FRONTEND=noninteractive
ENV HOME=/root

# Install essential system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    wget \
    git \
    sudo \
    locales \
    && rm -rf /var/lib/apt/lists/* \
    && locale-gen en_US.UTF-8

ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8
ENV LANGUAGE=en_US:en

# -----------------------------------------------------------------------------
# Stage 2: Build Tools
# -----------------------------------------------------------------------------
FROM system-base AS build-tools

# Install build essentials and development tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------------------------------------------------------
# Stage 3: CLI Tools
# -----------------------------------------------------------------------------
FROM build-tools AS cli-tools

# Install CLI utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    vim \
    unzip \
    zip \
    tar \
    jq \
    gnupg \
    tmux \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------------------------------------------------------
# Stage 4: Python
# -----------------------------------------------------------------------------
FROM cli-tools AS python-base

# Install Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && ln -sf /root/.local/bin/uv /usr/local/bin/uv

# -----------------------------------------------------------------------------
# Stage 5: Node.js
# -----------------------------------------------------------------------------
FROM python-base AS nodejs-base

# Install Node.js 20.x LTS
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------------------------------------------------------
# Stage 6: GitHub CLI
# -----------------------------------------------------------------------------
FROM nodejs-base AS github-cli

ARG HOST_ARCH=amd64

# Install GitHub CLI from official binary release
RUN if [ "$HOST_ARCH" = "arm64" ]; then \
        GH_ARCH="arm64"; \
    else \
        GH_ARCH="amd64"; \
    fi && \
    curl -fsSL https://github.com/cli/cli/releases/download/v2.55.0/gh_2.55.0_linux_${GH_ARCH}.tar.gz -o /tmp/gh.tar.gz && \
    tar -xzf /tmp/gh.tar.gz -C /tmp && \
    mv /tmp/gh_2.55.0_linux_${GH_ARCH}/bin/gh /usr/local/bin/ && \
    mv /tmp/gh_2.55.0_linux_${GH_ARCH}/bin/ghd /usr/local/bin/ 2>/dev/null || true && \
    rm -rf /tmp/gh.tar.gz /tmp/gh_2.55.0_linux_${GH_ARCH}

# -----------------------------------------------------------------------------
# Stage 7: NPM Global Packages
# -----------------------------------------------------------------------------
FROM github-cli AS npm-packages

# Install claude-code-router globally
RUN npm install -g @musistudio/claude-code-router

# -----------------------------------------------------------------------------
# Stage 8: Playwright
# -----------------------------------------------------------------------------
FROM npm-packages AS playwright

# Install playwright and playwright MCP with bundled Chromium
RUN npm install -g playwright \
    && npx playwright install --with-deps chromium

# Create symlinks for browser compatibility
RUN ln -sf /root/.cache/ms-playwright/chromium-*/chrome-linux/chrome /usr/bin/google-chrome 2>/dev/null || true && \
    ln -sf /root/.cache/ms-playwright/chromium-*/chrome-linux/chrome /usr/bin/chromium 2>/dev/null || true

# -----------------------------------------------------------------------------
# Stage 9: Claude Code
# -----------------------------------------------------------------------------
FROM playwright AS claude

# Copy Claude Code install script
COPY install.sh /tmp/install.sh

# Create required directories
RUN mkdir -p /root/.claude/downloads

# Install Claude Code
RUN chmod +x /tmp/install.sh \
    && /tmp/install.sh stable \
    && rm -f /tmp/install.sh \
    && rm -f /usr/local/bin/claude \
    && cp /root/.local/bin/claude /usr/local/bin/claude && chmod +x /usr/local/bin/claude

# -----------------------------------------------------------------------------
# Stage 10: User Setup
# -----------------------------------------------------------------------------
FROM claude AS user-setup

# Create sudoers.d directory for non-root sudo access
RUN mkdir -p /etc/sudoers.d \
    && echo "agentizer ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/agentizer \
    && chmod 440 /etc/sudoers.d/agentizer

# Add non-root user
RUN useradd -m -s /bin/bash agentizer \
    && mkdir -p /home/agentizer/.claude/downloads \
    && chown -R agentizer:agentizer /home/agentizer

# -----------------------------------------------------------------------------
# Stage 11: Final
# -----------------------------------------------------------------------------
FROM user-setup AS final

# Set working directory
WORKDIR /workspace

# Copy entrypoint script
COPY entrypoint.sh /usr/local/bin/entrypoint
RUN chmod 755 /usr/local/bin/entrypoint

# Install claude plugin as agentizer user during build
USER agentizer
ENV HOME=/home/agentizer
RUN claude mcp add -s user playwright npx @playwright/mcp@latest --headless

# Stay as agentizer user for runtime
# Default command
ENTRYPOINT ["/usr/local/bin/entrypoint"]
CMD ["/bin/bash"]
