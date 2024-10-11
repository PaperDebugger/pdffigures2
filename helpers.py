def create_full_text(json_data):
    # Extract the abstract text
    abstract_text = json_data.get("abstractText", {}).get("text", "")
    print(abstract_text)

    # Initialize full text with abstract
    full_text = abstract_text + "\n\n"

    # Iterate through sections
    for section in json_data.get("sections", []):
        # Add section title if present
        if isinstance(section, dict) and "title" in section and isinstance(section["title"], dict):
            full_text += section["title"].get("text", "") + "\n\n"

        # Add paragraphs
        if isinstance(section, dict) and "paragraphs" in section:
            for paragraph in section["paragraphs"]:
                if isinstance(paragraph, dict) and "text" in paragraph:
                    full_text += paragraph["text"] + " "
            full_text += "\n\n"

    return full_text.strip()


# Usage
def process_json(json_data):
    try:
        full_text = create_full_text(json_data)
        return full_text
    except Exception as e:
        print(f"Error processing JSON: {e}")
        return None
