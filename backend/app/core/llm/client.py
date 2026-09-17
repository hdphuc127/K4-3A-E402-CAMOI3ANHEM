"""Real implementations of ``app.core.prompts.schemas.LlmCaller``.

One ``LlmProvider`` per vendor (Gemini, OpenAI, OpenRouter, ...), and one
``ProviderLlmCaller`` that just dispatches to whichever provider instance was
registered under that name at construction time. Adding a new vendor means
writing one more ``LlmProvider`` and registering it in ``_build_providers`` -
``ProviderLlmCaller`` itself never has to change.

The prompts layer never imports an LLM SDK (see
``test_package_imports_with_no_env_and_no_sdks`` in
``tests/unit/test_prompts_schema_compat.py``), so each provider imports its
SDK lazily, inside ``generate()``, only once it is actually called.
"""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import Protocol

from app.core.config import settings
from app.core.prompts.schemas import PromptBundle, Provider

_GEMINI_MODEL = "gemini-2.0-flash"
_OPENAI_MODEL = "gpt-4o-mini"


class LlmProvider(Protocol):
    """One vendor's way of turning a ``PromptBundle`` into raw output text.

    Must raise on any transport/auth failure instead of swallowing it -
    ``fallback._call_once`` is the layer responsible for catching, classifying
    and degrading, so implementations must not do that themselves.
    """

    async def generate(self, bundle: PromptBundle, *, timeout_s: float) -> str: ...


class GeminiProvider:
    """Calls Gemini through ``google-generativeai``."""

    def __init__(self, api_key: str, *, model: str = _GEMINI_MODEL) -> None:
        self._api_key = api_key
        self._model = model

    async def generate(self, bundle: PromptBundle, *, timeout_s: float) -> str:
        import google.generativeai as genai

        genai.configure(api_key=self._api_key)
        args = bundle.as_gemini_args()
        # A fresh model instance per call: system_instruction carries the
        # per-request canary token (guardrail G8), so it can't be cached.
        model = genai.GenerativeModel(
            self._model, system_instruction=args["system_instruction"]
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
    """Calls any Chat Completions-compatible endpoint.

    Covers both OpenAI itself and OpenRouter (same request/response shape,
    OpenRouter just needs a different ``base_url`` and model name).
    """

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
    """Implements ``LlmCaller`` by dispatching to an injected provider map."""

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
            msg = f"{provider} auth error: no client configured for provider {provider!r}"
            raise RuntimeError(msg)
        return await impl.generate(bundle, timeout_s=timeout_s)


def _build_providers() -> dict[str, LlmProvider]:
    """Only register a provider once its API key is actually configured.

    Requesting an unregistered provider raises at call time (classified as
    LLM_AUTH_ERROR by fallback.py), so run_guarded_generation degrades
    gracefully instead of the app failing to start when a key is missing.
    """
    providers: dict[str, LlmProvider] = {}
    if settings.gemini_api_key:
        providers["gemini"] = GeminiProvider(settings.gemini_api_key)
    if settings.openai_api_key:
        providers["openai"] = OpenAiCompatibleProvider(
            settings.openai_api_key, model=settings.default_llm_model or _OPENAI_MODEL
        )
    if settings.openrouter_api_key:
        providers["openrouter"] = OpenAiCompatibleProvider(
            settings.openrouter_api_key,
            model=settings.openrouter_model,
            base_url="https://openrouter.ai/api/v1",
        )
    return providers


default_llm_caller = ProviderLlmCaller(_build_providers())
