"""Concrete LLM provider clients used by the prompt pipeline."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import Protocol

from app.core.config import settings
from app.core.prompts.schemas import PromptBundle, Provider

_GEMINI_MODEL = "gemini-2.0-flash"
_OPENAI_MODEL = "gpt-4o-mini"


class LlmProvider(Protocol):
    async def generate(self, bundle: PromptBundle, *, timeout_s: float) -> str: ...


class GeminiProvider:
    def __init__(self, api_key: str, *, model: str = _GEMINI_MODEL) -> None:
        self._api_key = api_key
        self._model = model

    async def generate(self, bundle: PromptBundle, *, timeout_s: float) -> str:
        import google.generativeai as genai

        genai.configure(api_key=self._api_key)
        args = bundle.as_gemini_args()
        model = genai.GenerativeModel(
            self._model,
            system_instruction=args["system_instruction"],
        )
        response = await asyncio.wait_for(
            asyncio.to_thread(
                model.generate_content,
                args["contents"],
                generation_config=args["generation_config"],
            ),
            timeout=timeout_s,
        )
        return response.text


class OpenAiCompatibleProvider:
    def __init__(
        self,
        api_key: str,
        *,
        model: str,
        base_url: str | None = None,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url

    async def generate(self, bundle: PromptBundle, *, timeout_s: float) -> str:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self._api_key, base_url=self._base_url)
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model=self._model,
                messages=bundle.as_openai_messages(),
                response_format=bundle.as_openai_response_format(),
                temperature=bundle.temperature,
                max_tokens=bundle.max_output_tokens,
            ),
            timeout=timeout_s,
        )
        return response.choices[0].message.content or ""


class ProviderLlmCaller:
    def __init__(self, providers: Mapping[str, LlmProvider]) -> None:
        self._providers = dict(providers)

    async def __call__(
        self,
        bundle: PromptBundle,
        *,
        provider: Provider,
        timeout_s: float,
    ) -> str:
        impl = self._providers.get(provider)
        if impl is None:
            raise RuntimeError(f"{provider} auth error: no client configured")
        return await impl.generate(bundle, timeout_s=timeout_s)


def _build_providers() -> dict[str, LlmProvider]:
    providers: dict[str, LlmProvider] = {}
    if settings.gemini_api_key:
        providers["gemini"] = GeminiProvider(settings.gemini_api_key)
    if settings.openai_api_key:
        providers["openai"] = OpenAiCompatibleProvider(
            settings.openai_api_key,
            model=settings.default_llm_model or _OPENAI_MODEL,
        )
    if settings.openrouter_api_key:
        providers["openrouter"] = OpenAiCompatibleProvider(
            settings.openrouter_api_key,
            model=settings.openrouter_model,
            base_url="https://openrouter.ai/api/v1",
        )
    return providers


default_llm_caller = ProviderLlmCaller(_build_providers())
