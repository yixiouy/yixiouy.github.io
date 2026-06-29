#!/usr/bin/env python3
"""
build.py — Convert Markdown pages to HTML for local preview.

Usage:
    python build.py

Reads each .md file, converts it to HTML using the Jekyll layout template,
and writes the result as a .html file in the same directory.

No dependencies beyond Python stdlib. For better Markdown rendering,
optionally install: pip install markdown
"""

import re
import os
import sys

# Try to import the markdown library for full rendering
try:
    import markdown as md_lib
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False


# --- Minimal Markdown to HTML converter (stdlib only) ---

def convert_markdown(text):
    """Convert basic Markdown to HTML. Falls back to simple regex if no library."""
    if HAS_MARKDOWN:
        # Preprocess: add blank line before list items so the library detects them
        text = re.sub(r'\n(\s*[-*+]\s+)', r'\n\n\1', text)
        text = re.sub(r'\n(\s*\d+\.\s+)', r'\n\n\1', text)
        return md_lib.markdown(text, extensions=['extra', 'smarty'])

    # --- Fallback: minimal-but-functional converter ---
    lines = text.split('\n')
    out = []
    in_list = False
    in_olist = False
    in_blockquote = False
    buf = []

    def flush_paragraph():
        nonlocal buf
        if buf:
            content = ' '.join(buf)
            content = inline_format(content)
            out.append(f'<p>{content}</p>')
            buf = []

    def flush_list():
        nonlocal in_list, in_olist
        if in_list:
            out.append('</ul>')
            in_list = False
        if in_olist:
            out.append('</ol>')
            in_olist = False

    for line in lines:
        # Blank line
        if line.strip() == '':
            flush_paragraph()
            flush_list()
            if in_blockquote:
                out.append('</blockquote>')
                in_blockquote = False
            continue

        # Headings
        m = re.match(r'^(#{1,6})\s+(.+)$', line)
        if m:
            flush_paragraph()
            flush_list()
            level = len(m.group(1))
            text = inline_format(m.group(2))
            out.append(f'<h{level}>{text}</h{level}>')
            continue

        # Horizontal rule
        if re.match(r'^[-*_]{3,}\s*$', line):
            flush_paragraph()
            flush_list()
            out.append('<hr>')
            continue

        # Blockquote
        m = re.match(r'^>\s?(.*)$', line)
        if m:
            flush_paragraph()
            flush_list()
            if not in_blockquote:
                out.append('<blockquote>')
                in_blockquote = True
            content = inline_format(m.group(1))
            out.append(f'<p>{content}</p>')
            continue

        # Unordered list
        m = re.match(r'^[-*+]\s+(.+)$', line)
        if m:
            flush_paragraph()
            if not in_list:
                out.append('<ul>')
                in_list = True
            content = inline_format(m.group(1))
            out.append(f'<li>{content}</li>')
            continue

        # Ordered list
        m = re.match(r'^\d+\.\s+(.+)$', line)
        if m:
            flush_paragraph()
            if not in_olist:
                out.append('<ol>')
                in_olist = True
            content = inline_format(m.group(1))
            out.append(f'<li>{content}</li>')
            continue

        # Regular paragraph text
        buf.append(line)

    # Clean up any remaining open elements
    flush_paragraph()
    flush_list()
    if in_blockquote:
        out.append('</blockquote>')

    return '\n'.join(out)


def inline_format(text):
    """Handle inline Markdown formatting: bold, italic, links, code."""
    # Bold **text** or __text__
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)
    # Italic *text* or _text_
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'_(.+?)_', r'<em>\1</em>', text)
    # Inline code `text`
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    # Links [text](url)
    text = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', text)
    return text


# --- Front matter parser ---

def parse_front_matter(text):
    """Extract YAML-like front matter from Markdown text."""
    fm = {}
    body = text
    if text.startswith('---'):
        parts = text.split('---', 2)
        if len(parts) >= 3:
            for line in parts[1].strip().split('\n'):
                m = re.match(r'^(\w+):\s*(.*)$', line)
                if m:
                    key = m.group(1)
                    val = m.group(2).strip().strip('"').strip("'")
                    # Handle booleans
                    if val.lower() == 'true':
                        val = True
                    elif val.lower() == 'false':
                        val = False
                    fm[key] = val
            body = parts[2]
    return fm, body


# --- Template rendering ---

def render_page(template, content, title="", show_photo=False):
    """Insert content into the template."""
    html = template

    # Handle title FIRST (before replacing {{ site.title }})
    title_tag = '{{ page.title }} — {{ site.title }}'
    if title:
        html = html.replace(title_tag, f'{title} — Your Name')
    else:
        html = html.replace(title_tag, 'Your Name')

    # Insert content
    html = html.replace('{{ content }}', content)

    # Replace remaining {{ site.title }} and {{ page.title }}
    html = html.replace('{{ site.title }}', 'Your Name')
    html = html.replace('{{ page.title }}', title)

    # Handle show_photo conditional
    if show_photo:
        html = html.replace('{% if page.show_photo %}', '')
        html = re.sub(r'\{%\s*endif\s*%\}', '', html, count=1)
    else:
        html = re.sub(
            r'\{%\s*if page\.show_photo\s*%\}.*?\{%\s*endif\s*%\}',
            '',
            html,
            flags=re.DOTALL
        )

    # Remove any remaining Liquid tags
    html = re.sub(r'\{%[^%]*%\}', '', html)
    html = re.sub(r'\{\{[^}]*\}\}', '', html)

    return html


# --- Main build process ---

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Load both templates
    home_layout_path = os.path.join(base_dir, '_layouts', 'home.html')
    page_layout_path = os.path.join(base_dir, '_layouts', 'page.html')

    if not os.path.exists(home_layout_path):
        print("Error: _layouts/home.html not found!")
        sys.exit(1)
    if not os.path.exists(page_layout_path):
        print("Error: _layouts/page.html not found!")
        sys.exit(1)

    with open(home_layout_path, 'r', encoding='utf-8') as f:
        home_template = f.read()
    with open(page_layout_path, 'r', encoding='utf-8') as f:
        page_template = f.read()

    # Find all .md files in the base directory
    md_files = [f for f in os.listdir(base_dir) if f.endswith('.md')]

    built = 0
    for md_file in md_files:
        md_path = os.path.join(base_dir, md_file)
        html_path = os.path.join(base_dir, md_file.replace('.md', '.html'))

        with open(md_path, 'r', encoding='utf-8') as f:
            raw = f.read()

        fm, body = parse_front_matter(raw)
        content_html = convert_markdown(body)
        title = fm.get('title', '')
        show_photo = fm.get('show_photo', False)
        layout_name = fm.get('layout', 'page')

        # Pick template based on layout
        if layout_name == 'home':
            template = home_template
        else:
            template = page_template

        result = render_page(template, content_html, title=title, show_photo=show_photo)

        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(result)

        print(f"  OK  {md_file} -> {os.path.basename(html_path)}  [{layout_name}]")
        built += 1

    print(f"\nBuilt {built} pages. Open index.html in your browser to preview.")
    print("(Run 'python -m http.server 8000' in this folder for best results)")


if __name__ == '__main__':
    main()
