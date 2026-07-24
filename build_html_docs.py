import os
import re
import markdown
import webbrowser

def convert_md_to_html(md_path, html_path, title):
    if not os.path.exists(md_path):
        print(f"File not found: {md_path}")
        return

    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Pre-process mermaid codeblocks so mermaid.js can render them
    # Replace ```mermaid with <div class="mermaid">
    def mermaid_replacer(match):
        code = match.group(1).strip()
        return f'<div class="mermaid">\n{code}\n</div>'

    md_processed = re.sub(r'```mermaid\s*\n(.*?)\n```', mermaid_replacer, md_content, flags=re.DOTALL)

    # Convert Markdown to HTML
    html_body = markdown.markdown(
        md_processed,
        extensions=['tables', 'fenced_code', 'codehilite', 'toc']
    )

    html_document = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <!-- GitHub Markdown CSS -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.5.1/github-markdown.min.css">
    <!-- Highlight.js for Code Highlighting -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
    <!-- Mermaid.js for Rendering Architecture Diagrams -->
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        body {{
            box-sizing: border-box;
            min-width: 200px;
            max-width: 1200px;
            margin: 0 auto;
            padding: 45px;
            background-color: #0d1117;
            color: #c9d1d9;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }}
        .markdown-body {{
            background-color: #0d1117;
            color: #c9d1d9;
        }}
        .mermaid {{
            background-color: #161b22;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            display: flex;
            justify-content: center;
        }}
        @media (max-width: 767px) {{
            body {{
                padding: 15px;
            }}
        }}
    </style>
</head>
<body>
    <article class="markdown-body">
        {html_body}
    </article>

    <script>
        hljs.highlightAll();
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'dark',
            securityLevel: 'loose'
        }});
    </script>
</body>
</html>
'''

    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_document)

    print(f"Generated HTML: {html_path}")

if __name__ == '__main__':
    base_dir = r"C:\Source\AIFriday"
    
    docs = [
        (os.path.join(base_dir, "skills", "tcs-hackathon-blueprint", "SKILL.md"), os.path.join(base_dir, "skills", "tcs-hackathon-blueprint", "SKILL.html"), "TCS Hackathon Master Blueprint Skill"),
        (os.path.join(base_dir, "ARCHITECTURE.md"), os.path.join(base_dir, "ARCHITECTURE.html"), "System Architecture Documentation"),
        (os.path.join(base_dir, "README.md"), os.path.join(base_dir, "README.html"), "Project Overview README")
    ]

    for md_p, html_p, title in docs:
        convert_md_to_html(md_p, html_p, title)
