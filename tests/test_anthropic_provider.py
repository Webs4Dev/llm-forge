import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from core.generate import generate
from providers.anthropic import AnthropicProvider


def main():
    provider = AnthropicProvider(
        model="claude-haiku-4-5"
    )

    ticket = (
        "I was charged twice for my monthly subscription. "
        "Please check the duplicate charge."
    )

    result = generate(
        provider=provider,
        ticket_text=ticket,
        temperature=0.0,
        max_tokens=500,
    )

    print("\n" + "=" * 60)
    print("ANTHROPIC TEST")
    print("=" * 60)

    print("\nOutput:")
    print(result.text)

    print("\nUsage:")
    print(f"Input tokens:  {result.input_tokens}")
    print(f"Output tokens: {result.output_tokens}")

    print("\nLatency:")
    print(f"TTFT:          {result.ttft:.4f}s")
    print(f"Total latency: {result.total_latency:.4f}s")

    print("=" * 60)


if __name__ == "__main__":
    main()