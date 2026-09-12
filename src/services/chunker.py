import re
from typing import List, Tuple


class TranscriptChunker:
    """Chunks transcripts by speaker turn, with overflow handling."""

    def __init__(self, max_tokens_per_chunk: int = 2000, overlap_tokens: int = 200):
        self.max_tokens = max_tokens_per_chunk
        self.overlap = overlap_tokens

    def tokenize(self, text: str) -> List[str]:
        """Simple whitespace tokenization."""
        return text.split()

    def chunk_transcript(self, transcript_text: str) -> List[Tuple[str, str, str]]:
        """
        Chunk transcript content by speaker turn.
        Returns list of (speaker_name, timestamp, content) tuples.

        Format in transcript:
          Speaker Name (HH:MM:SS):
          Speaker's dialogue here...

          Another Speaker (HH:MM:SS):
          Their dialogue...
        """
        speaker_pattern = r'^([^(]+)\s*\((\d{2}:\d{2}:\d{2})\):\s*'

        chunks = []
        lines = transcript_text.split('\n')

        current_speaker = None
        current_timestamp = None
        current_content_lines = []

        for line in lines:
            if not line.strip():
                if current_content_lines:
                    current_content_lines.append(line)
                continue

            match = re.match(speaker_pattern, line)
            if match:
                # New speaker turn
                if current_content_lines:
                    chunks.append((
                        current_speaker,
                        current_timestamp,
                        '\n'.join(current_content_lines).strip()
                    ))

                current_speaker = match.group(1).strip()
                current_timestamp = match.group(2)
                content_start = match.end()
                current_content_lines = [line[content_start:].strip()] if line[content_start:].strip() else []
            else:
                current_content_lines.append(line)

        # Save last chunk
        if current_content_lines:
            chunks.append((current_speaker, current_timestamp, '\n'.join(current_content_lines).strip()))

        # Split large chunks (>max_tokens) with overlap
        final_chunks = []
        for speaker, timestamp, content in chunks:
            tokens = self.tokenize(content)
            if len(tokens) <= self.max_tokens:
                final_chunks.append((speaker, timestamp, content))
            else:
                for i in range(0, len(tokens), self.max_tokens - self.overlap):
                    chunk_tokens = tokens[i:i + self.max_tokens]
                    chunk_text = ' '.join(chunk_tokens)
                    final_chunks.append((speaker, timestamp, chunk_text))

        return final_chunks


def chunk_episode(episode_content: str) -> List[dict]:
    """
    Parse and chunk a single episode transcript.

    Input: Raw markdown file content (frontmatter + transcript)
    Output: List of chunk dicts with episode metadata
    """
    lines = episode_content.split('\n')

    frontmatter = {}
    transcript_start = 0

    # Parse YAML frontmatter
    if lines and lines[0].strip() == '---':
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == '---':
                transcript_start = i + 1
                break
            if ':' in line:
                key, value = line.split(':', 1)
                frontmatter[key.strip()] = value.strip().strip("'\"")

    # Extract transcript (skip title headings, find "## Transcript" section)
    transcript_lines = lines[transcript_start:]
    transcript_text = '\n'.join(transcript_lines)

    # Find "## Transcript" section
    transcript_idx = transcript_text.find('## Transcript')
    if transcript_idx != -1:
        transcript_text = transcript_text[transcript_idx + len('## Transcript'):].lstrip('\n')

    # Chunk the transcript
    chunker = TranscriptChunker()
    chunks = chunker.chunk_transcript(transcript_text)

    # Build output
    result = []
    for speaker, timestamp, content in chunks:
        result.append({
            'episode_title': frontmatter.get('title', 'Unknown'),
            'guest_name': frontmatter.get('guest', 'Unknown'),
            'speaker_name': speaker,
            'timestamp': timestamp,
            'content': content,
            'video_url': frontmatter.get('youtube_url', '')
        })

    return result
