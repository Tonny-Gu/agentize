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
# Stage 1: Base
# -----------------------------------------------------------------------------
FROM ubuntu:24.04 AS base

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV HOME=/root

# Install base packages, Node.js 20.x LTS, and Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    wget \
    git \
    vim \
    unzip \
    zip \
    tar \
    build-essential \
    libssl-dev \
    pkg-config \
    sudo \
    jq \
    gnupg \
    tmux \
    python3 \
    python3-pip \
    python3-venv \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && ln -sf /root/.local/bin/uv /usr/local/bin/uv

# Install GitHub CLI from official binary release
# Use HOST_ARCH build arg for architecture-specific binary selection
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

# Install claude-code-router globally
RUN npm install -g @musistudio/claude-code-router

# Install playwright and playwright MCP with bundled Chromium
RUN npm install -g playwright \
    && npx playwright install --with-deps chromium

# Create symlinks for browser compatibility (playwright's bundled chromium)
RUN ln -sf /root/.cache/ms-playwright/chromium-*/chrome-linux/chrome /usr/bin/google-chrome 2>/dev/null || true && \
    ln -sf /root/.cache/ms-playwright/chromium-*/chrome-linux/chrome /usr/bin/chromium 2>/dev/null || true

# -----------------------------------------------------------------------------
# Stage 7: Claude Code
# -----------------------------------------------------------------------------
FROM base AS claude

# Copy Claude Code install script
COPY install.sh /tmp/install.sh

# Create required directories
RUN mkdir -p /root/.claude/downloads

# Install Claude Code (silent mode - assumes install.sh works in container)
RUN chmod +x /tmp/install.sh \
    && /tmp/install.sh stable \
    && rm -f /tmp/install.sh \
    && rm -f /usr/local/bin/claude \
    && cp /root/.local/bin/claude /usr/local/bin/claude && chmod +x /usr/local/bin/claude

# -----------------------------------------------------------------------------
# Stage 8: Final
# -----------------------------------------------------------------------------
FROM claude AS final

# Create sudoers.d directory for non-root sudo access
RUN mkdir -p /etc/sudoers.d \
    && echo "agentizer ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/agentizer \
    && chmod 440 /etc/sudoers.d/agentizer

# Add non-root user
RUN useradd -m -s /bin/bash agentizer \
    && mkdir -p /home/agentizer/.claude/downloads \
    && chown -R agentizer:agentizer /home/agentizer

# Set working directory
WORKDIR /workspace

# Set environment for agentizer
ENV HOME=/home/agentizer

# Copy entrypoint script
COPY entrypoint.sh /usr/local/bin/entrypoint
RUN chmod +x /usr/local/bin/entrypoint

# Switch to non-root user
USER agentizer

# Default command
ENTRYPOINT ["/usr/local/bin/entrypoint"]
CMD ["/bin/bash"]
