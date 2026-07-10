from config import settings
from google import genai
from openai import AsyncOpenAI
from google.genai import types
from config import settings

gemini_client = genai.Client(api_key=settings.api_key)
openai_client = AsyncOpenAI(api_key=settings.openai_api_key)

def format_for_openai(contents):
    if isinstance(contents, str):
        return [{"role": "user", "content": contents}]
    messages = []
    for msg in contents:
        messages.append({
            "role": "assistant" if msg["role"] == "model" else msg["role"],
            "content": msg["parts"][0]["text"]
        })
    return messages

async def generate_stream(contents, provider: str = "gemini"):
    if provider == "gemini":
        async for chunk in await gemini_client.aio.models.generate_content_stream(
            model="gemini-2.5-flash",
            contents=contents
        ):
            yield chunk.text

    elif provider == "openai":
        formatted = format_for_openai(contents)
        async for chunk in await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=formatted,
            stream=True
        ):
            yield chunk.choices[0].delta.content or ""

    else:
        raise ValueError(f"unknown provider: {provider}")