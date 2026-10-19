FROM python:3.13-slim
WORKDIR /service
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .
USER 65532:65532
ENV AIYUCHA_MCP_BIND=0.0.0.0
EXPOSE 8765
CMD ["aiyucha-mcp"]
