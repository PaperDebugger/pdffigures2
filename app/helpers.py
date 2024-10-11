import re


def extract_sections(text):
    # Initialize variables
    sections = {}
    current_main_section = None
    current_content = []

    # Split text into lines
    lines = text.split("\n")

    # Combine lines to handle headings that span multiple lines
    combined_lines = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue  # Skip empty lines
        # Check if this line is a number and the next line is possibly a heading
        if re.match(r"^\d+$", line) and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            # Assume that if the next line is not empty, it's a heading
            if next_line:
                combined_line = f"{line} {next_line}"
                combined_lines.append(combined_line)
                i += 2  # Skip the next line as it's part of the heading
            else:
                combined_lines.append(line)
                i += 1
        else:
            combined_lines.append(line)
            i += 1

    # Define heading patterns
    main_heading_pattern = re.compile(r"^(\d+)\s+(.*)$")  # Matches headings like '1 INTRODUCTION'
    sub_heading_pattern = re.compile(r"^(\d+\.\d+)\s+(.*)$")  # Matches headings like '2.1 Preliminary'
    # Known headings (case-insensitive)
    known_headings = {
        "Abstract",
        "Title",
        "Introduction",
        "Background",
        "Related Work",
        "Evaluation",
        "Figure",
        "Table",
        "Motivation",
        "Technical Section",
        "Conclusion",
        "References",
        "Appendix",
        # "Format",
        # "Acknowledgements",
        # "Methodology",
        # "Results",
        # "Discussion",
    }
    known_headings_lower = [h.lower() for h in known_headings]

    for idx, line in enumerate(combined_lines):
        line = line.strip()
        if not line:
            continue  # Skip empty lines

        # Check for main numbered heading
        m_main = main_heading_pattern.match(line)
        if m_main and "." not in m_main.group(1):
            # Save current section
            if current_main_section is not None:
                content = " ".join(current_content).strip()
                sections[current_main_section] = content
            # Start new main section
            section_number = m_main.group(1)
            section_title = m_main.group(2).strip()
            current_main_section = f"{section_number} {section_title}"
            current_content = []
            continue

        # Check for unnumbered heading (known headings)
        if line.lower() in known_headings_lower:
            # Save current section
            if current_main_section is not None:
                content = " ".join(current_content).strip()
                sections[current_main_section] = content
            # Start new main section
            current_main_section = line.strip()
            current_content = []
            continue

        # For subheadings and other content
        # We include subheadings in the content of the current main section
        # So we can check for subheadings and append them to content
        m_sub = sub_heading_pattern.match(line)
        if m_sub:
            # It's a subheading
            sub_section_number = m_sub.group(1)
            sub_section_title = m_sub.group(2).strip()
            current_content.append(f"{sub_section_number} {sub_section_title}")
            continue

        # Append line to current content
        if current_main_section is None:
            # If no current section, start with 'Abstract'
            current_main_section = "Abstract"
        current_content.append(line)

    # Save the last section
    if current_main_section is not None:
        content = " ".join(current_content).strip()
        sections[current_main_section] = content
    return sections


def create_full_text(json_data):
    # Extract the abstract text
    abstract_text = json_data.get("abstractText", {}).get("text", "")

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
