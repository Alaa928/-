import re
import os
from collections import OrderedDict

input_file = "/home/ubuntu/الفصل_الثالث_الموسع.md"
output_file = "/home/ubuntu/الفصل_الثالث_للتحويل.md"

if not os.path.exists(input_file):
    print(f"Error: Input file not found at {input_file}")
    exit(1)

with open(input_file, 'r', encoding='utf-8') as f:
    content = f.read()

footnotes_data = OrderedDict()
bibliography_details = set()

# Regex to find citation markers: ^Number^Citation details (assuming details are on the same line)
# Using a non-greedy match for citation details
citation_pattern = re.compile(r'\^(\d+)\^([^
^]+)')

processed_content = content
current_footnote_index = 1
processed_offset = 0
matches = list(citation_pattern.finditer(content))

# Sort matches by start position to process in order
matches.sort(key=lambda m: m.start())

for match in matches:
    # original_note_number_str = match.group(1) # Original number is ignored
    citation_details = match.group(2).strip()
    original_match_text = match.group(0)

    # Use sequential footnote numbers
    actual_note_number = current_footnote_index

    # Store citation details for footnotes and bibliography
    # Use the raw detail as key to handle duplicates for bibliography
    if citation_details not in footnotes_data:
         footnotes_data[citation_details] = {
             'first_occurrence_index': actual_note_number,
             'all_indices': [actual_note_number]
         }
         bibliography_details.add(citation_details) # Add unique details for bib
    else:
        # If detail already exists, just record the new index
        footnotes_data[citation_details]['all_indices'].append(actual_note_number)

    # Replace original marker and details with Pandoc footnote reference
    # Need to adjust indices due to previous replacements
    start_index = match.start() + processed_offset
    end_index = match.end() + processed_offset
    replacement_text = f'[^{actual_note_number}]'

    processed_content = processed_content[:start_index] + replacement_text + processed_content[end_index:]
    # Update offset for next replacement
    processed_offset += len(replacement_text) - len(original_match_text)

    current_footnote_index += 1

# --- Generate Footnote Definitions for Pandoc ---
# Format: [^Number]: Footnote text.
footnotes_definitions = "\n\n---\n\n## الهوامش\n\n"
footnote_mapping = {}
sequential_footnote_num = 1
for details, data in footnotes_data.items():
    # Create the footnote text (basic formatting)
    # For simplicity, just using the captured details. Chicago formatting needs manual refinement later.
    note_text = f"{sequential_footnote_num}. {details}"
    # Map all original occurrences to this single definition
    for index in data['all_indices']:
        footnote_mapping[index] = note_text
    sequential_footnote_num += 1

# Append definitions in sequential order
for i in range(1, current_footnote_index):
    if i in footnote_mapping:
         # Ensure the definition format is correct for Pandoc
         footnotes_definitions += f"[^{i}]: {footnote_mapping[i]}\n"

# --- Generate Bibliography Section (Basic List) ---
# Chicago bibliography requires specific formatting and sorting (Author Last, First.)
# This basic version just lists unique citations. Manual formatting needed.
bibliography_section = "\n\n---\n\n## قائمة المراجع\n\n"
sorted_bib_list = sorted(list(bibliography_details))
for item in sorted_bib_list:
    # Basic formatting - needs manual Chicago style refinement
    # Attempt basic Author Last, First extraction if possible
    parts = item.split(',', 1)
    if len(parts) == 2 and ' ' in parts[0] and not any(char.isdigit() for char in parts[0]): # Simple check for Author Name
        author = parts[0].strip()
        rest = parts[1].strip()
        # Try to guess last name
        name_parts = author.split()
        if len(name_parts) > 1:
            last_name = name_parts[-1]
            first_names = " ".join(name_parts[:-1])
            bib_entry = f"{last_name}, {first_names}. {rest}"
        else:
            bib_entry = f"{author}. {rest}" # Single name author
    else:
        bib_entry = item # Fallback to original detail

    # Ensure it ends with a period
    if not bib_entry.endswith('.'):
        bib_entry += '.'
    bibliography_section += f"- {bib_entry}\n"

# --- Combine and Write Output ---
# Append footnote definitions *after* the main content for Pandoc
final_content = processed_content + footnotes_definitions + bibliography_section

with open(output_file, 'w', encoding='utf-8') as f:
    f.write(final_content)

print(f"تمت معالجة الهوامش والمراجع بشكل مبدئي، وحفظ الملف في: {output_file}")
print(f"إجمالي الهوامش المستخدمة: {current_footnote_index - 1}")
print(f"إجمالي المراجع الفريدة: {len(bibliography_details)}")
print("ملاحظة: تم إنشاء الهوامش وقائمة المراجع بشكل أساسي. قد تحتاج قائمة المراجع إلى تنسيق يدوي إضافي لتتوافق تمامًا مع أسلوب شيكاغو (الفرز والترتيب الدقيق للأسماء).")

