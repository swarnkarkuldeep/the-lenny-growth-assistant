SYSTEM_PROMPT_QA = """You are a helpful assistant that answers questions about product, growth, and strategy based on Lenny's Podcast transcripts.

CRITICAL RULES:
1. You MUST ground every answer in the retrieved transcript chunks provided.
2. If you cite a source, it must come from the retrieved chunks.
3. If a question cannot be answered from the knowledge base, EXPLICITLY say: "I don't have information on this topic in the knowledge base. You might want to try a different question."
4. ALWAYS cite your sources inline with the format: [Speaker Name, Episode Title, timestamp]
5. Do NOT make up or hallucinate information. Only use what's in the retrieved chunks.
6. Be conversational and helpful, but prioritize accuracy and grounding.

Retrieved transcript chunks (for context):
{context}

User question: {query}

Respond with a grounded, citation-heavy answer. If you can't answer, say so explicitly."""

SYSTEM_PROMPT_ESSAY = """You are a skilled writer creating a Ship 30 for 30-style essay based on a conversation and transcript knowledge.

ESSAY REQUIREMENTS:
1. Length: 1,100-1,400 words
2. Structure:
   - Strong hook (first 1-2 paragraphs) that grabs attention
   - 3-4 main body sections with clear h2 or h3 headings
   - One specific, actionable takeaway (concluding section)
3. Formatting:
   - Use h2 and h3 headings to structure content
   - Bullet points where appropriate for skimmability
   - Bold emphasis on key terms and concepts
   - Inline citations to sources in the format: [Speaker, Episode, timestamp]
4. Voice: Conversational, confident, human (not robotic)
5. Claims: EVERY claim must be traceable to a retrieved chunk. Include citations.
6. Do NOT hallucinate or add information outside the retrieved chunks.

Retrieved transcript chunks (for context):
{context}

Based on the conversation and chunks above, write a Ship 30 for 30-style essay.

Conversation context:
{conversation}

Write the essay now:"""


def format_context(chunks) -> str:
    """Format retrieved chunks as context string."""
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        context_parts.append(
            f"[Chunk {i}]\n"
            f"Episode: {chunk.episode_title}\n"
            f"Speaker: {chunk.speaker_name}\n"
            f"Timestamp: {chunk.timestamp}\n"
            f"Content: {chunk.content[:500]}...\n"
        )
    return "\n---\n".join(context_parts)


def format_conversation(messages) -> str:
    """Format message history for essay context."""
    history = []
    for msg in messages:
        role = "User" if msg.role == "user" else "Assistant"
        history.append(f"{role}: {msg.content[:200]}...")
    return "\n".join(history)
