import re
import os
from collections import OrderedDict

input_file = "/home/ubuntu/الفصل_الثالث_الموسع.md"
output_file = "/home/ubuntu/الفصل_الثالث_للباندوك.md"

if not os.path.exists(input_file):
    print(f"Error: Input file not found at {input_file}")
    exit(1)

with open(input_file, 'r', encoding='utf-8') as f:
    content = f.read()

footnotes_data = OrderedDict()
bibliography_details = set()

# Corrected Regex: Match ^Number^ followed by any characters until the next ^ or end of line
citation_pattern = re.compile(r'\^(\d+)\^([^\^\n]+)')

processed_content = content
current_footnote_index = 1
processed_offset = 0
matches = list(citation_pattern.finditer(content))

# Sort matches by start position to process in order
matches.sort(key=lambda m: m.start())

footnote_definitions_dict = {}

for match in matches:
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
         # Store the definition text mapped to its first occurrence index
         footnote_definitions_dict[actual_note_number] = f"{actual_note_number}. {citation_details}"
    else:
        # If detail already exists, just record the new index
        footnotes_data[citation_details]['all_indices'].append(actual_note_number)

    # Replace original marker and details with Pandoc footnote reference
    start_index = match.start() + processed_offset
    end_index = match.end() + processed_offset
    replacement_text = f'[^{actual_note_number}]'

    processed_content = processed_content[:start_index] + replacement_text + processed_content[end_index:]
    processed_offset += len(replacement_text) - len(original_match_text)

    current_footnote_index += 1

# --- Generate Footnote Definitions Section for Pandoc ---
footnotes_definitions_section = "\n\n---\n\n## الهوامش\n\n"
# Append definitions in sequential order based on their first appearance
for i in range(1, current_footnote_index):
    if i in footnote_definitions_dict:
        # Format for Pandoc: [^index]: Text.
        footnotes_definitions_section += f"[^{i}]: {footnote_definitions_dict[i]}\n"

# --- Generate Bibliography Section (Basic List - Requires Manual Chicago Formatting) ---
bibliography_section = "\n\n---\n\n## قائمة المراجع\n\n"
sorted_bib_list = sorted(list(bibliography_details))
for item in sorted_bib_list:
    # Basic formatting attempt (needs refinement for proper Chicago)
    parts = item.split(',', 1)
    bib_entry = item # Default
    if len(parts) == 2 and ' ' in parts[0].strip() and not any(char.isdigit() for char in parts[0].strip()):
        author = parts[0].strip()
        rest = parts[1].strip()
        name_parts = author.split()
        if len(name_parts) > 1:
            last_name = name_parts[-1]
            first_names = " ".join(name_parts[:-1])
            bib_entry = f"{last_name}, {first_names}. {rest}"
        else:
            bib_entry = f"{author}. {rest}"
    if not bib_entry.endswith('.'):
        bib_entry += '.'
    bibliography_section += f"- {bib_entry}\n"

# --- Combine and Write Output ---
# Append footnote definitions *after* the main content for Pandoc
final_content = processed_content + footnotes_definitions_section + bibliography_section

# Remove the original inline footnote definitions section if it exists
final_content = re.sub(r'\n---\n\*\*الهوامش:\*\*\n.*?(?=\n## |\Z)', '', final_content, flags=re.DOTALL)
final_content = re.sub(r'\n---\n\*\*هوامش إضافية للخاتمة:\*\*\n.*?(?=\Z)', '', final_content, flags=re.DOTALL)


with open(output_file, 'w', encoding='utf-8') as f:
    f.write(final_content)

print(f"تم إعداد الملف للتوافق مع Pandoc وحفظه في: {output_file}")
print(f"إجمالي الهوامش المستخدمة: {current_footnote_index - 1}")
print(f"إجمالي المراجع الفريدة: {len(bibliography_details)}")
print("ملاحظة: تم إنشاء الهوامش وقائمة المراجع بشكل أساسي. قد تحتاج قائمة المراجع إلى تنسيق يدوي إضافي لتتوافق تمامًا مع أسلوب شيكاغو.")

