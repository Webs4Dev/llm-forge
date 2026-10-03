def normalize_json_output(text):
    text = text.strip()

    if text.startswith("```json") and text.endswith("```"):
        text = text[7:-3].strip()

    elif text.startswith("```") and text.endswith("```"):
        text = text[3:-3].strip()

    return text