from dotenv import load_dotenv
from litellm import completion
from loguru import logger

load_dotenv("./LLMService/.env")


messages = [{"content": "Hello, how are you?", "role": "user"}]

# Call the completion function, referencing the model in the proxy's config
response = completion(model="litellm_proxy/gemini", messages=messages)

logger.info(response.choices[0].message.content)
