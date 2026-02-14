FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        git curl ca-certificates gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
        | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
        | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt-get update && apt-get install -y --no-install-recommends gh \
    && npm install -g @openai/codex @google/gemini-cli \
    && npm cache clean --force \
    && curl -LsSf https://astral.sh/uv/install.sh | env CARGO_HOME=/usr/local UV_INSTALL_DIR=/usr/local/bin sh \
    && apt-get purge -y --auto-remove gnupg \
    && rm -rf /var/lib/apt/lists/* /tmp/* /root/.npm /root/.cache

RUN useradd -m -s /bin/bash reviewer
WORKDIR /app
RUN chown reviewer:reviewer /app
USER reviewer
ENV HOME=/home/reviewer

RUN curl -fsSL https://claude.ai/install.sh | bash \
    && rm -rf /tmp/*
ENV PATH="/home/reviewer/.local/bin:$PATH"

COPY --chown=reviewer:reviewer pyproject.toml uv.lock ./
RUN uv sync --frozen && rm -rf /home/reviewer/.cache/uv
ENV PATH="/app/.venv/bin:$PATH"

COPY --chown=reviewer:reviewer . .
COPY --chown=reviewer:reviewer entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
