# LitellmProxy

This service acts as a proxy to Large Language Models using [LiteLLM](https://github.com/BerriAI/litellm). It is configured to proxy requests to the Gemini model.

## Configuration

1.  **API Key**: Create a `.env` file from the `env.example` and add your Gemini API key:
    ```bash
    cp env.example .env
    # Now edit .env and add your key
    ```
    **`.env`**
    ```
    GEMINI_API_KEY=Your_key
    ```

2.  **Model Configuration**: The `litellm_config.yaml` file defines the models that are available through the proxy. By default, it is configured to use `gemini/gemini-2.5-flash-lite`.

    ```yaml
    model_list:
      - model_name: gemini
        litellm_params:
          model: gemini/gemini-2.5-flash-lite
    ```

## Running the service

To start the proxy service, run the following command from the root of the project:

```bash
docker compose up litellm-proxy
```

The proxy will be available at `http://localhost:4000`.
