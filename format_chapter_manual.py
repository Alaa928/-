import re
import os

# Function to format footnote according to Chicago Notes style (simplified)
def format_chicago_note(note_text):
    note_text = note_text.strip()
    if note_text and note_text[-1] not in ['.', '?', '!']:
        note_text += '.'
    return note_text

# Function to format bibliography entry according to Chicago Bibliography style (simplified)
def format_chicago_bib(note_text):
    note_text = note_text.strip()
    parts = note_text.split(',')
    author = parts[0].strip()
    name_parts = author.split()
    formatted_author = author # Default if formatting fails
    rest_of_entry = ",".join(parts[1:]).strip() if len(parts) > 1 else ""

    # Attempt to format author name (Last, First) - very basic
    if len(name_parts) >= 2:
        # Check if it looks like an Arabic name (heuristic: no obvious Latin characters)
        is_arabic_name = all('\u0600' <= char <= '\u06FF' or char.isspace() for char in author)
        if not is_arabic_name and name_parts[0][0].isupper() and name_parts[-1][0].isupper(): # Likely Western name
            last_name = name_parts[-1]
            first_names = " ".join(name_parts[:-1])
            formatted_author = f"{last_name}, {first_names}"
        # For Arabic names, keep as is for simplicity in this script, Chicago requires transliteration/specific rules
        # formatted_author = author # Kept as is

    bib_entry = f"{formatted_author}. {rest_of_entry}" if rest_of_entry else formatted_author

    if bib_entry and bib_entry[-1] != '.':
        bib_entry += '.'
    return bib_entry

# Read the expanded chapter content
input_file = "/home/ubuntu/الفصل_الثالث_الموسع.md"
output_file = "/home/ubuntu/الفصل_الثالث_المنسق_يدويا.md" # New output file

try:
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
except FileNotFoundError:
    print(f"Error: Input file {input_file} not found.")
    exit(1)
except Exception as e:
    print(f"Error reading file {input_file}: {e}")
    exit(1)

# Separate main content from the footnotes section more reliably
# Find the start of the footnotes section marker
footnote_marker = "\n---\n**الهوامش:**\n"
marker_pos = content.find(footnote_marker)

if marker_pos == -1:
    print("Error: Footnotes section marker '--- الهوامش:' not found.")
    # As a fallback, try to find the last '---' before the end
    marker_pos = content.rfind("\n---\n")
    if marker_pos != -1:
        print("Warning: Using last '---' as potential start of footnotes. Results may be inaccurate.")
        footnote_content_raw = content[marker_pos:].strip()
        main_content = content[:marker_pos].strip()
        # Further check if it looks like footnotes
        if not re.search(r'\^\d+\^', footnote_content_raw):
             print("Error: Fallback marker position does not seem to contain footnotes.")
             exit(1)
    else:
        print("Error: Could not find any potential footnote section marker.")
        exit(1)
else:
    main_content = content[:marker_pos].strip()
    footnote_content_raw = content[marker_pos + len(footnote_marker):].strip()

# Parse individual footnotes from the raw footnote content
# Handles footnotes potentially spanning multiple lines
footnote_lines = footnote_content_raw.split('\n')
footnotes_raw = {}
current_num = None
current_text = ""
for line in footnote_lines:
    line = line.strip()
    if not line: continue # Skip empty lines
    match = re.match(r'\^(\d+)\^\s*(.*)', line)
    if match:
        if current_num is not None:
            footnotes_raw[current_num] = current_text.strip()
        current_num = match.group(1)
        current_text = match.group(2).strip()
    elif current_num is not None:
        # Append to the current footnote text if it's a continuation line
        current_text += " " + line
# Add the last footnote parsed
if current_num is not None:
    footnotes_raw[current_num] = current_text.strip()

# Check if footnotes were parsed
if not footnotes_raw:
    print("Error: No footnotes could be parsed from the footnote section.")
    # Check if they might be inline (unlikely given previous structure)
    exit(1)

# --- Processing --- 

processed_notes_mapping = {}
bibliography_entries = []
final_notes_list = []
current_footnote_index = 1
superscript_map = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
missing_notes_markers = []

# Function to replace markers in the text
def replace_marker_func(match):
    global current_footnote_index
    original_marker = match.group(1)

    if original_marker in processed_notes_mapping:
        # Already processed this note number, use its assigned index
        new_index = processed_notes_mapping[original_marker]
    elif original_marker in footnotes_raw:
        # First time seeing this note number, process it
        new_index = current_footnote_index
        processed_notes_mapping[original_marker] = new_index

        original_note_text = footnotes_raw[original_marker]
        formatted_note = format_chicago_note(original_note_text)
        formatted_bib = format_chicago_bib(original_note_text)

        final_notes_list.append(f"{new_index}. {formatted_note}")
        bibliography_entries.append(formatted_bib)

        current_footnote_index += 1
    else:
        # Marker exists in text but not in parsed footnotes
        print(f"Warning: Footnote marker ^{original_marker}^ found in text but definition is missing or unparsed.")
        missing_notes_markers.append(original_marker)
        return "[?]" # Replace with placeholder

    # Return the new index as superscript
    return str(new_index).translate(superscript_map)

# Replace markers in the main content using the function
formatted_content = re.sub(r'\^(\d+)\^', replace_marker_func, main_content)

# --- Final Assembly --- 

# Create the final formatted footnotes section
footnotes_section = "\n\n---\n**الهوامش**\n\n" + "\n".join(final_notes_list)

# Create the final formatted bibliography section
# Remove duplicates and sort alphabetically (simple sort)
unique_bib_entries = sorted(list(set(bibliography_entries)))
bibliography_section = "\n\n---\n**قائمة المراجع**\n\n" + "\n".join([f"- {entry}" for entry in unique_bib_entries])

# Combine everything
final_document = formatted_content + footnotes_section + bibliography_section

# Add warning about missing notes if any
if missing_notes_markers:
    final_document += "\n\n---\n**تحذير:** لم يتم العثور على تعريفات للهوامش التالية في النص الأصلي: " + ", ".join(sorted(list(set(missing_notes_markers))))

# Write the formatted document
try:
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(final_document)
    print(f"Formatted chapter saved to {output_file}")
except Exception as e:
    print(f"Error writing file {output_file}: {e}")
    exit(1)

