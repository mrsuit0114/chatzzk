FROM ghcr.io/berriai/litellm:main-latest

WORKDIR /app

COPY app/servers/llm_proxy_server/litellm_config.yaml ./config.yaml

EXPOSE 4000

CMD ["--config", "/app/config.yaml", "--detailed_debug"]
