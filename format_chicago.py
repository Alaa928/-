import re
import os
from collections import OrderedDict

# --- Chicago Style Formatting Helpers (Simplified) ---

def format_chicago_note(details, note_number):
    # Basic formatting - attempts to identify common patterns
    # This is a simplified version and might need manual refinement
    details = details.strip()
    # Example: Assume format "Author, Title (Publication Info), Page."
    # More sophisticated parsing would be needed for real-world complexity
    return f"{note_number}. {details}"

def format_chicago_bib(details):
    # Basic formatting - attempts to identify common patterns
    # This is a simplified version and might need manual refinement
    details = details.strip()
    # Example: Reorder Author, handle titles, etc.
    # Try to extract Author for sorting (assuming 'Name,' or 'Name,')
    match = re.match(r"^([^,]+),", details)
    author_last_name = match.group(1).strip() if match else "ZZZ" # Default for sorting if no author found
    # Simple formatting for bibliography entry
    # Remove page numbers if present at the end
    details_no_page = re.sub(r",\s*p(p)?\.\s*\d+[-\d+]*\.?$", "", details).strip()
    if details_no_page.endswith("."):
        return details_no_page, author_last_name
    else:
        return f"{details_no_page}.", author_last_name

# --- Main Processing Logic ---

input_file = "/home/ubuntu/الفصل_الثالث_الموسع.md"
output_file = "/home/ubuntu/الفصل_الثالث_المنسق_شيكاغو.md"

if not os.path.exists(input_file):
    print(f"Error: Input file not found at {input_file}")
    exit(1)

with open(input_file, 'r', encoding='utf-8') as f:
    content = f.read()

footnotes = OrderedDict()
bibliography = {}

# Regex to find citation markers and associated text
# Assumes format: Text.^Number^Citation details potentially spanning lines until next marker or double newline
# This regex is complex and might capture too much or too little.
# Let's try a simpler assumption: ^Number^Citation details on the same line.
processed_content = content

# Find all potential citations first
citation_matches = list(re.finditer(r'\^(\d+)\^([^
^]+)', content))

current_footnote_index = 1
processed_offset = 0

for match in citation_matches:
    note_number_str = match.group(1)
    citation_details = match.group(2).strip()
    original_match_text = match.group(0)

    # Use sequential footnote numbers instead of the ones in the text initially
    actual_note_number = current_footnote_index

    # Store citation details for formatting
    if actual_note_number not in footnotes:
        footnotes[actual_note_number] = {
            'details': citation_details,
            'formatted_note': format_chicago_note(citation_details, actual_note_number)
        }
        # Prepare bibliography entry (handle duplicates based on details)
        bib_entry, sort_key = format_chicago_bib(citation_details)
        if citation_details not in bibliography:
             bibliography[citation_details] = {'entry': bib_entry, 'sort_key': sort_key}

    # Replace original marker and details with superscript footnote reference
    replacement_text = f'[^{actual_note_number}]'
    start_index = match.start() + processed_offset
    end_index = match.end() + processed_offset

    processed_content = processed_content[:start_index] + replacement_text + processed_content[end_index:]
    processed_offset += len(replacement_text) - len(original_match_text)

    current_footnote_index += 1


# --- Generate Footnotes Section ---
footnotes_section = "\n\n---\n\n## الهوامش\n\n"
for num, data in footnotes.items():
    footnotes_section += f"{data['formatted_note']}\n"

# --- Generate Bibliography Section ---
bibliography_section = "\n\n---\n\n## قائمة المراجع\n\n"
# Sort bibliography items alphabetically by author's last name (using sort_key)
sorted_bib_items = sorted(bibliography.values(), key=lambda x: x['sort_key'])
for item in sorted_bib_items:
    bibliography_section += f"{item['entry']}\n"

# --- Combine and Write Output ---
final_content = processed_content + footnotes_section + bibliography_section

with open(output_file, 'w', encoding='utf-8') as f:
    f.write(final_content)

print(f"الفصل المنسق بنظام شيكاغو تم حفظه في: {output_file}")
print(f"إجمالي عدد الهوامش: {len(footnotes)}")
print(f"إجمالي عدد المراجع في القائمة: {len(bibliography)}")

