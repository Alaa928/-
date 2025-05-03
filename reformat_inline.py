import re
import os

input_file = "/home/ubuntu/الفصل_الثالث_الموسع.md"
output_file_md = "/home/ubuntu/الفصل_الثالث_InlineCite.md"

if not os.path.exists(input_file):
    print(f"Error: Input file not found at {input_file}")
    exit(1)

with open(input_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Remove old footnote/bibliography sections added in previous steps
content = re.sub(r'\n---\n\n## الهوامش\n.*?(?=\n\n---\n\n## قائمة المراجع|$)', '', content, flags=re.DOTALL)
content = re.sub(r'\n---\n\n## قائمة المراجع\n.*', '', content, flags=re.DOTALL)
content = re.sub(r'\n---\n\*\*الهوامش:\*\*\n.*?(?=\n## |\Z)', '', content, flags=re.DOTALL)
content = re.sub(r'\n---\n\*\*هوامش إضافية للخاتمة:\*\*\n.*?(?=\Z)', '', content, flags=re.DOTALL)

# Regex to find citation markers: ^Number^Citation details (non-greedy)
citation_pattern = re.compile(r'\^(\d+)\^([^\^\n]+)')

# Split content into paragraphs (handle multiple newlines)
paragraphs = re.split(r'\n{2,}', content)

processed_paragraphs = []

for para in paragraphs:
    if not para.strip():
        continue

    citations_in_para = []
    # Find all citations within the paragraph
    matches = list(citation_pattern.finditer(para))

    # Store citation details
    for match in matches:
        citation_details = match.group(2).strip()
        # Basic formatting: remove trailing period if exists for consistency
        if citation_details.endswith('.'):
            citation_details = citation_details[:-1]
        citations_in_para.append(citation_details)

    # Remove citation markers and details from the paragraph text
    cleaned_para = citation_pattern.sub('', para).strip()

    # Append the collected citations at the end of the paragraph
    if citations_in_para:
        # Join multiple citations with a semicolon
        citations_text = "; ".join(citations_in_para)
        # Add parentheses and ensure a period at the end
        cleaned_para += f" ({citations_text})."
    elif cleaned_para and not cleaned_para.endswith(('.', ':', '?', '!')):
         # Add trailing period if paragraph doesn't end with punctuation and had no citations
         cleaned_para += '.'

    processed_paragraphs.append(cleaned_para)

# Join paragraphs back with double newlines
final_content = "\n\n".join(processed_paragraphs)

with open(output_file_md, 'w', encoding='utf-8') as f:
    f.write(final_content)

print(f"تمت إعادة تنسيق الملف مع المراجع المضمنة وحفظه في: {output_file_md}")

