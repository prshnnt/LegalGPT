from pathlib import Path

def get_system_prompt() -> str:
    prompt_path = Path(__file__).parent / "SYSTEM_PROMPT.md"
    return prompt_path.read_text(encoding="utf-8")