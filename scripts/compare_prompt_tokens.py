from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

try:
    import tiktoken
except ImportError:
    print("tiktoken is not installed.")
    print("Run: pip install tiktoken")
    sys.exit(1)


POLICY_V1 = PROJECT_ROOT / "data" / "policy" / "policy-v1.txt"
POLICY_V2 = PROJECT_ROOT / "data" / "policy" / "policy-v2.txt"

PROMPT_V1 = PROJECT_ROOT / "data" / "prompts" / "tickets-v1.txt"
PROMPT_V2 = PROJECT_ROOT / "data" / "prompts" / "tickets-v2.txt"


def load_file(path):
    return path.read_text(encoding="utf-8")


def count_tokens(text, encoding):
    return len(encoding.encode(text))


def main():
    encoding = tiktoken.get_encoding("cl100k_base")

    policy_v1 = load_file(POLICY_V1)
    policy_v2 = load_file(POLICY_V2)

    prompt_v1 = load_file(PROMPT_V1)
    prompt_v2 = load_file(PROMPT_V2)

    policy_tokens_v1 = count_tokens(policy_v1, encoding)
    policy_tokens_v2 = count_tokens(policy_v2, encoding)

    prompt_tokens_v1 = count_tokens(prompt_v1, encoding)
    prompt_tokens_v2 = count_tokens(prompt_v2, encoding)

    total_v1 = policy_tokens_v1 + prompt_tokens_v1
    total_v2 = policy_tokens_v2 + prompt_tokens_v2

    reduction = total_v1 - total_v2
    reduction_percent = (reduction / total_v1) * 100

    print()
    print("=" * 60)
    print("PROMPT TOKEN COMPARISON")
    print("=" * 60)

    print()
    print("POLICY")
    print("-" * 60)
    print(f"V1 tokens: {policy_tokens_v1}")
    print(f"V2 tokens: {policy_tokens_v2}")
    print(f"Reduction: {policy_tokens_v1 - policy_tokens_v2}")

    policy_reduction = (
        (policy_tokens_v1 - policy_tokens_v2)
        / policy_tokens_v1
        * 100
    )

    print(f"Reduction %: {policy_reduction:.2f}%")

    print()
    print("PROMPT")
    print("-" * 60)
    print(f"V1 tokens: {prompt_tokens_v1}")
    print(f"V2 tokens: {prompt_tokens_v2}")
    print(f"Reduction: {prompt_tokens_v1 - prompt_tokens_v2}")

    prompt_reduction = (
        (prompt_tokens_v1 - prompt_tokens_v2)
        / prompt_tokens_v1
        * 100
    )

    print(f"Reduction %: {prompt_reduction:.2f}%")

    print()
    print("TOTAL STATIC INSTRUCTIONS")
    print("-" * 60)
    print(f"V1 total: {total_v1}")
    print(f"V2 total: {total_v2}")
    print(f"Tokens saved per request: {reduction}")
    print(f"Reduction: {reduction_percent:.2f}%")

    print()
    print("300 REQUEST WORKLOAD")
    print("-" * 60)
    print(f"V1 instruction tokens: {total_v1 * 300}")
    print(f"V2 instruction tokens: {total_v2 * 300}")
    print(f"Total tokens saved: {reduction * 300}")

    print()
    print("=" * 60)


if __name__ == "__main__":
    main()