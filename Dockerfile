FROM python:3.14-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.11.32 /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install dependencies, compiling bytecode now so cold starts don't pay for it
ENV UV_COMPILE_BYTECODE=1
RUN uv sync --frozen --no-dev

# Run commands from the synced venv directly rather than via `uv run`, which would
# re-sync the default `dev` group at container start
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code and migrations
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini start.sh ./

# Expose port
EXPOSE 8000

# Start the application (migrations run separately; see README)
CMD ["./start.sh"]
