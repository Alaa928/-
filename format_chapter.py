import re
import os

# Function to format footnote according to Chicago Notes style (simplified)
def format_chicago_note(note_text):
    # Basic formatting - assumes input is somewhat structured
    # More sophisticated parsing might be needed for complex cases
    note_text = note_text.strip()
    # Ensure it ends with a period if not already ending with punctuation
    if note_text and note_text[-1] not in ['.', '?', '!']:
        note_text += '.'
    return note_text

# Function to format bibliography entry according to Chicago Bibliography style (simplified)
def format_chicago_bib(note_text):
    # Basic formatting - assumes input is somewhat structured
    # Attempts to switch author name order (Last, First) if possible
    note_text = note_text.strip()
    parts = note_text.split(',')
    # Check if the first part looks like a name (e.g., "First Last" or "أحمد داود أوغلو")
    author = parts[0].strip()
    name_parts = author.split()
    if len(name_parts) >= 2:
        # Simple assumption: last word is the last name
        last_name = name_parts[-1]
        first_names = " ".join(name_parts[:-1])
        formatted_author = f"{last_name}, {first_names}"
        # Reconstruct the entry with formatted author
        rest_of_entry = ",".join(parts[1:]).strip()
        bib_entry = f"{formatted_author}. {rest_of_entry}"
    else:
        # If it doesn't look like a name or has only one part, use as is
        bib_entry = note_text

    # Ensure it ends with a period
    if bib_entry and bib_entry[-1] != ".":
        bib_entry += "."
    return bib_entry

# Read the expanded chapter content
input_file = "/home/ubuntu/الفصل_الثالث_الموسع.md"
output_file = "/home/ubuntu/الفصل_الثالث_المنسق.md"

try:
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
except FileNotFoundError:
    print(f"Error: Input file {input_file} not found.")
    exit(1)
except Exception as e:
    print(f"Error reading file {input_file}: {e}")
    exit(1)

# Extract footnotes section
footnote_section_match = re.search(r"\n---\n\*\*الهوامش:\*\*\n+(.*?)$", content, re.DOTALL | re.MULTILINE)

if not footnote_section_match:
    print("Error: Footnotes section not found or not in expected format.")
    # Attempt to find footnotes differently if the marker is missing
    footnote_matches = list(re.finditer(r'\^(\d+)\^\s*(.*?)(?=\n\^|\Z)', content.split("## خاتمة الفصل الثالث")[1] if "## خاتمة الفصل الثالث" in content else content, re.DOTALL))
    if not footnote_matches:
        print("Could not find footnotes using alternative method either.")
        exit(1)
    else:
        print("Warning: Standard footnote section marker not found, attempting alternative extraction.")
        footnotes_raw = {match.group(1): match.group(2).strip() for match in footnote_matches}
        # Remove footnotes from main content if extracted alternatively
        # This part is tricky and might remove wanted text if not careful
        # For now, let's assume the original structure with the marker is needed
        # If the marker is truly missing, manual intervention or a more robust script is required.
        # We will proceed assuming the first search worked for the logic below.
        # If it didn't, the script will likely fail later or produce incorrect results.
        # Let's add a check here
        print("Exiting due to inability to reliably find and separate footnotes.")
        exit(1)
else:
    footnote_content = footnote_section_match.group(1).strip()
    # Remove the footnote section from the main content
    main_content = content[:footnote_section_match.start()].strip()

    # Parse individual footnotes
    footnote_lines = footnote_content.split('\n')
    footnotes_raw = {}
    current_num = None
    current_text = ""
    for line in footnote_lines:
        match = re.match(r'\^(\d+)\^\s*(.*)', line)
        if match:
            if current_num is not None:
                footnotes_raw[current_num] = current_text.strip()
            current_num = match.group(1)
            current_text = match.group(2)
        elif current_num is not None:
            current_text += " " + line.strip()
    if current_num is not None: # Add the last footnote
        footnotes_raw[current_num] = current_text.strip()

# Renumber footnotes sequentially and format them
formatted_notes = {}
bibliography_entries = []
note_mapping = {}
current_footnote_index = 1

# Find all footnote markers in the main content
footnote_markers_in_text = re.findall(r'\^(\d+)\^', main_content)

processed_markers = set()
final_notes_list = []

for marker in footnote_markers_in_text:
    if marker in footnotes_raw and marker not in processed_markers:
        original_note_text = footnotes_raw[marker]
        formatted_note = format_chicago_note(original_note_text)
        formatted_bib = format_chicago_bib(original_note_text)

        # Store the formatted note with the new sequential index
        final_notes_list.append(f"{current_footnote_index}. {formatted_note}")
        bibliography_entries.append(formatted_bib)

        # Store the mapping from old marker to new index
        note_mapping[marker] = current_footnote_index
        processed_markers.add(marker)
        current_footnote_index += 1
    elif marker in note_mapping:
        # This marker refers to an already processed note, use its assigned index
        pass # The replacement logic below handles this
    elif marker not in footnotes_raw:
        print(f"Warning: Footnote marker ^{marker}^ found in text but corresponding note definition is missing.")
        # Decide how to handle missing notes, e.g., replace with [?] or keep marker
        # For now, we'll map it to a placeholder to avoid errors, but it needs fixing
        if marker not in note_mapping:
             note_mapping[marker] = "[?]" # Placeholder for missing note

# Replace old markers with new superscript numbers in the main content
def replace_marker(match):
    old_marker = match.group(1)
    if old_marker in note_mapping:
        new_index = note_mapping[old_marker]
        # Simple superscript for now, proper formatting might need specific tools (like pandoc later)
        superscript_map = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
        return str(new_index).translate(superscript_map)
    else:
        # Keep the original marker if mapping failed (e.g., missing note)
        return match.group(0)

formatted_content = re.sub(r'\^(\d+)\^', replace_marker, main_content)

# Create the final formatted footnotes section
footnotes_section = "\n\n---\n**الهوامش**\n\n" + "\n".join(final_notes_list)

# Create the final formatted bibliography section
# Remove duplicates and sort alphabetically
unique_bib_entries = sorted(list(set(bibliography_entries)))
bibliography_section = "\n\n---\n**قائمة المراجع**\n\n" + "\n".join([f"- {entry}" for entry in unique_bib_entries])

# Combine everything
final_document = formatted_content + footnotes_section + bibliography_section

# Write the formatted document
try:
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(final_document)
    print(f"Formatted chapter saved to {output_file}")
except Exception as e:
    print(f"Error writing file {output_file}: {e}")
    exit(1)

