import logging
import re
from typing import List

from src.schemas import RetrievedChunk

logger = logging.getLogger(__name__)


class EssayValidator:
    """Validates generated essays against Ship 30/30 requirements."""

    @staticmethod
    def count_words(text: str) -> int:
        """Count words in text."""
        return len(text.split())

    @staticmethod
    def check_word_count(text: str) -> bool:
        """Check if essay is 1,100-1,400 words."""
        count = EssayValidator.count_words(text)
        return 1100 <= count <= 1400

    @staticmethod
    def check_headings(text: str) -> bool:
        """Check if essay has at least one h2 or h3 heading."""
        return bool(re.search(r'^(#{2,3})\s', text, re.MULTILINE))

    @staticmethod
    def check_takeaway(text: str) -> bool:
        """Check if essay mentions a takeaway or key insight."""
        keywords = ["takeaway", "key insight", "main point", "remember", "key takeaway"]
        return any(kw in text.lower() for kw in keywords)

    @staticmethod
    def check_citations(text: str) -> bool:
        """Check if essay has at least one citation."""
        return '[' in text and ']' in text

    @staticmethod
    def check_claims_traceable(text: str, chunks: List[RetrievedChunk]) -> bool:
        """
        Check if citations reference the retrieved chunks actually used as context.
        This is a simplified check; a full implementation would do semantic matching.
        """
        if not chunks:
            return False

        chunk_speakers = set(c.speaker_name for c in chunks)
        citation_pattern = r'\[(.*?)\]'
        citations = re.findall(citation_pattern, text)

        return any(
            any(speaker in citation for speaker in chunk_speakers)
            for citation in citations
        )

    @staticmethod
    def validate(text: str, chunks: List[RetrievedChunk]) -> dict:
        """Validate essay against all Ship 30/30 requirements."""
        return {
            "word_count_ok": EssayValidator.check_word_count(text),
            "has_headings": EssayValidator.check_headings(text),
            "has_takeaway": EssayValidator.check_takeaway(text),
            "has_citations": EssayValidator.check_citations(text),
            "all_claims_traceable": EssayValidator.check_claims_traceable(text, chunks),
            "compliance_passed": all([
                EssayValidator.check_word_count(text),
                EssayValidator.check_headings(text),
                EssayValidator.check_takeaway(text),
                EssayValidator.check_citations(text),
                EssayValidator.check_claims_traceable(text, chunks),
            ]),
            "word_count": EssayValidator.count_words(text),
        }
