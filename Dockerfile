# Pinned versions — bump deliberately when upgrading
FROM docker.n8n.io/n8nio/n8n:2.26.8

USER root

# Copy uv binary from the official uv image (statically linked — works on Alpine)
COPY --from=ghcr.io/astral-sh/uv:0.12.10 /uv /usr/local/bin/uv

# Copy workspace config and source owned by the node user from the start
COPY --chown=node:node pyproject.toml uv.lock .python-version /home/node/project/
COPY --chown=node:node src/ /home/node/project/src/

USER node

# Pre-install Python and all dependencies — runs as node so ~/.local is accessible
RUN cd /home/node/project && uv sync --frozen --no-dev
