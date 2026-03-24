"""Generation client using Gemini (free tier)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tenacity import retry, stop_after_attempt, wait_exponential

if TYPE_CHECKING:
    from google.genai import Client

SYSTEM_INSTRUCTION = """Responde sempre em português europeu. És um assistente jurídico que ajuda \
cidadãos a perceber a Constituição da República Portuguesa.

Regras:
1. Responde APENAS com base nos trechos da Constituição fornecidos abaixo. \
Se a resposta não estiver nos trechos, diz "Não encontrei nos artigos disponíveis."
2. Cita sempre os artigos que usaste (ex: "Art. 13.º").
3. Sê conciso (3-6 frases) e usa linguagem acessível.
4. Não inventes artigos, números ou conteúdo.
5. Termina com um disclaimer breve: "Esta resposta não constitui aconselhamento jurídico."
"""


class Generator:
    def __init__(self, client: Client, *, model: str = "gemini-2.5-flash") -> None:
        self._client = client
        self._model = model

    @property
    def model(self) -> str:
        return self._model

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=15))
    def generate(self, question: str, context: str) -> str:
        from google.genai import types

        prompt = (
            f"Pergunta do cidadão: {question}\n\nTrechos relevantes da Constituição:\n\n{context}"
        )
        resp = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.2,
                max_output_tokens=1024,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        return (resp.text or "").strip()
