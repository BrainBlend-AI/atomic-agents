import os
from bs4 import BeautifulSoup
from markdownify import markdownify as md

# Paths
docs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "docs"))
single_dir = os.path.join(docs_dir, "_build", "singlehtml")
llms_txt_path = os.path.join(docs_dir, "llms.txt")

# Read single HTML index
html_file = os.path.join(single_dir, "index.html")
if not os.path.exists(html_file):
    print("Error: singlehtml output not found. Build with sphinx-build -b singlehtml.")
    exit(1)

with open(html_file, encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")
# Extract main documentation content
doc_main = soup.find("div", {"role": "main"}) or soup.find("div", class_="document")
content_html = str(doc_main) if doc_main else html

# Convert to Markdown
md_text = md(content_html)

# Write full documentation to llms.txt
with open(llms_txt_path, "w", encoding="utf-8") as out_f:
    out_f.write(md_text)

print(f"Generated full llms.txt at {llms_txt_path}")
