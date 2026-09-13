from uuid import uuid4

from src.schemas import RetrievedChunk
from src.services.essay import EssayValidator


def make_chunk(speaker="John Doe", episode="Episode Title", timestamp="00:12:34"):
    return RetrievedChunk(
        chunk_id=uuid4(),
        episode_title=episode,
        guest_name="Guest",
        speaker_name=speaker,
        timestamp=timestamp,
        content="Some transcript content.",
        video_url=None,
        similarity_score=0.9,
    )


def test_essay_word_count_validation():
    """Test word count validation."""
    short_essay = " ".join(["word"] * 500)
    assert not EssayValidator.check_word_count(short_essay)

    good_essay = " ".join(["word"] * 1200)
    assert EssayValidator.check_word_count(good_essay)

    long_essay = " ".join(["word"] * 1500)
    assert not EssayValidator.check_word_count(long_essay)


def test_essay_headings_validation():
    """Test heading validation."""
    with_headings = "## Main Topic\nSome content\n### Subtopic\nMore content"
    assert EssayValidator.check_headings(with_headings)

    without_headings = "Some content\nMore content"
    assert not EssayValidator.check_headings(without_headings)


def test_essay_takeaway_validation():
    """Test takeaway keyword detection."""
    with_takeaway = "Some content.\n\n## Key Takeaway\nDo this specific thing."
    assert EssayValidator.check_takeaway(with_takeaway)

    without_takeaway = "Some content without any concluding keyword."
    assert not EssayValidator.check_takeaway(without_takeaway)


def test_essay_citations_validation():
    """Test citation validation."""
    with_citations = "Some text [John Doe, Episode Title, 00:12:34] more text"
    assert EssayValidator.check_citations(with_citations)

    without_citations = "Some text without citations"
    assert not EssayValidator.check_citations(without_citations)


def test_essay_claims_traceable_validation():
    """Citations must reference a speaker present in the retrieved chunks."""
    chunks = [make_chunk(speaker="Jane Smith")]

    traceable = "Great insight here [Jane Smith, Episode Title, 00:01:00]."
    assert EssayValidator.check_claims_traceable(traceable, chunks)

    untraceable = "Great insight here [Someone Else, Episode Title, 00:01:00]."
    assert not EssayValidator.check_claims_traceable(untraceable, chunks)

    # No chunks at all means nothing can be traced.
    assert not EssayValidator.check_claims_traceable(traceable, [])


def test_essay_validate_full_compliance():
    """A well-formed essay should pass every check."""
    chunks = [make_chunk(speaker="Jane Smith")]
    body = " ".join(["word"] * 1150)
    essay = (
        "## Hook\n"
        f"{body}\n"
        "### Key Takeaway\n"
        "Remember this one specific, actionable insight [Jane Smith, Episode Title, 00:01:00]."
    )

    result = EssayValidator.validate(essay, chunks)

    assert result["word_count_ok"] is True
    assert result["has_headings"] is True
    assert result["has_takeaway"] is True
    assert result["has_citations"] is True
    assert result["all_claims_traceable"] is True
    assert result["compliance_passed"] is True
    assert result["word_count"] > 1100


def test_essay_validate_reports_failures():
    """An essay missing requirements should fail compliance with specific flags false."""
    chunks = [make_chunk(speaker="Jane Smith")]
    essay = "Too short and has no structure or supporting evidence."

    result = EssayValidator.validate(essay, chunks)

    assert result["word_count_ok"] is False
    assert result["has_headings"] is False
    assert result["has_takeaway"] is False
    assert result["has_citations"] is False
    assert result["compliance_passed"] is False
