import os

from litellm import completion
from loguru import logger

# Set the environment variables correctly for the LiteLLM client
os.environ["LITELLM_PROXY_API_KEY"] = "sk-1234"  # litellm proxy에서 정의하지 않아도 있어야하네
os.environ["LITELLM_PROXY_API_BASE"] = "http://host.docker.internal:4000"

messages = [{"content": "Hello, how are you?", "role": "user"}]

# Call the completion function, referencing the model in the proxy's config
response = completion(model="litellm_proxy/gemini", messages=messages)

logger.info(response.choices[0].message.content)
