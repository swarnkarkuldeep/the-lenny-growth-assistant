import logging
from abc import ABC, abstractmethod
from typing import List

import google.generativeai as genai
import requests

from src.config import settings
from src.prompts import (
    SYSTEM_PROMPT_ARTIFACT,
    SYSTEM_PROMPT_ESSAY,
    SYSTEM_PROMPT_QA,
    format_context,
    format_conversation,
)
from src.schemas import RetrievedChunk

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate_qa_response(self, query: str, chunks: List[RetrievedChunk]) -> str:
        """Generate Q&A response given query and context chunks."""
        pass

    @abstractmethod
    def generate_essay(self, conversation_history, chunks: List[RetrievedChunk]) -> str:
        """Generate Ship 30/30 essay based on conversation and chunks."""
        pass

    @abstractmethod
    def generate_artifact(
        self, conversation_history, chunks: List[RetrievedChunk], artifact_type: str
    ) -> str:
        """Generate a Markdown or HTML artifact based on conversation and chunks."""
        pass


def _build_artifact_prompt(conversation_history, chunks: List[RetrievedChunk], artifact_type: str) -> str:
    context = format_context(chunks)
    conversation = format_conversation(conversation_history)
    format_instructions = (
        "Return clean Markdown (headings, lists, bold/emphasis, links)."
        if artifact_type == "markdown"
        else (
            "Return a single self-contained HTML snippet using only these tags: "
            "h1, h2, h3, h4, h5, h6, p, ul, ol, li, strong, em, a, blockquote, code, pre. "
            "Do not include <script>, <iframe>, event handler attributes, or a <style> block."
        )
    )
    return SYSTEM_PROMPT_ARTIFACT.format(
        artifact_type=artifact_type,
        format_instructions=format_instructions,
        context=context,
        conversation=conversation,
    )


class GeminiProvider(LLMProvider):
    """Google Gemini via API."""

    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not configured")
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model_name = "gemini-flash-latest"
        self.model = genai.GenerativeModel(self.model_name)

    def generate_qa_response(self, query: str, chunks: List[RetrievedChunk]) -> str:
        """Generate Q&A response using Gemini."""
        context = format_context(chunks)
        prompt = SYSTEM_PROMPT_QA.format(context=context, query=query)

        try:
            response = self.model.generate_content(prompt)
            text = response.text
            logger.info(f"Gemini Q&A response generated ({len(text)} chars)")
            return text
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise RuntimeError(f"Gemini API error: {e}") from e

    def generate_essay(self, conversation_history, chunks: List[RetrievedChunk]) -> str:
        """Generate essay using Gemini."""
        context = format_context(chunks)
        conversation = format_conversation(conversation_history)
        prompt = SYSTEM_PROMPT_ESSAY.format(context=context, conversation=conversation)

        try:
            response = self.model.generate_content(prompt)
            text = response.text
            logger.info(f"Gemini essay generated ({len(text)} chars)")
            return text
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise RuntimeError(f"Gemini API error: {e}") from e

    def generate_artifact(
        self, conversation_history, chunks: List[RetrievedChunk], artifact_type: str
    ) -> str:
        """Generate a Markdown or HTML artifact using Gemini."""
        prompt = _build_artifact_prompt(conversation_history, chunks, artifact_type)

        try:
            response = self.model.generate_content(prompt)
            text = response.text
            logger.info(f"Gemini {artifact_type} artifact generated ({len(text)} chars)")
            return text
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise RuntimeError(f"Gemini API error: {e}") from e


class OllamaProvider(LLMProvider):
    """Local Ollama (llama3.2:3b)."""

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = "llama3.2:3b"

    def generate_qa_response(self, query: str, chunks: List[RetrievedChunk]) -> str:
        """Generate Q&A response using Ollama."""
        context = format_context(chunks)
        prompt = SYSTEM_PROMPT_QA.format(context=context, query=query)

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.7,
                },
                timeout=120,
            )
            response.raise_for_status()
            text = response.json()["response"]
            logger.info(f"Ollama Q&A response generated ({len(text)} chars)")
            return text
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Ollama unreachable: {e}")
            raise RuntimeError(f"Ollama unreachable at {self.base_url}") from e
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            raise RuntimeError(f"Ollama inference error: {e}") from e

    def generate_essay(self, conversation_history, chunks: List[RetrievedChunk]) -> str:
        """Generate essay using Ollama."""
        context = format_context(chunks)
        conversation = format_conversation(conversation_history)
        prompt = SYSTEM_PROMPT_ESSAY.format(context=context, conversation=conversation)

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.7,
                },
                timeout=180,
            )
            response.raise_for_status()
            text = response.json()["response"]
            logger.info(f"Ollama essay generated ({len(text)} chars)")
            return text
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Ollama unreachable: {e}")
            raise RuntimeError(f"Ollama unreachable at {self.base_url}") from e
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            raise RuntimeError(f"Ollama inference error: {e}") from e

    def generate_artifact(
        self, conversation_history, chunks: List[RetrievedChunk], artifact_type: str
    ) -> str:
        """Generate a Markdown or HTML artifact using Ollama."""
        prompt = _build_artifact_prompt(conversation_history, chunks, artifact_type)

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.7,
                },
                timeout=180,
            )
            response.raise_for_status()
            text = response.json()["response"]
            logger.info(f"Ollama {artifact_type} artifact generated ({len(text)} chars)")
            return text
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Ollama unreachable: {e}")
            raise RuntimeError(f"Ollama unreachable at {self.base_url}") from e
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            raise RuntimeError(f"Ollama inference error: {e}") from e


def get_llm_provider(provider: str) -> LLMProvider:
    """Factory function to get the selected provider."""
    if provider == "cloud":
        return GeminiProvider()
    elif provider == "local":
        return OllamaProvider()
    else:
        raise ValueError(f"Unknown provider: {provider}")
