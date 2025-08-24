import os
import shutil
import mistune
import json

def read_config():
    if os.path.exists("config.json"):
        with open("config.json", "r") as f:
            return json.load(f)
    else:
        with open("config.json", "w") as f:
            default_config = {
                "default_template": "base",
                "site_title": "My website"
            }
            json.dump(default_config, f, indent=4)
            return default_config

def convert_md_to_html(md_text):
    md_text = md_text.split("===")
    
    for idx, part in enumerate(md_text):
        md_text[idx] = part.strip()

    if len(md_text) > 1:
        metadata = md_text[0]
        md_text = md_text[1]
    else:
        metadata = None
        md_text = md_text[0]

    if metadata:
        metadata = json.loads(metadata)

        if "template" in metadata:
            template_name = metadata["template"]
        else:
            template_name = "base"
        
        if "title" in metadata:
            title = metadata["title"]
        else:
            title = read_config()["site_title"]
    else:
        template_name = "base"
        title = read_config()["site_title"]
    
    template_path = os.path.join("templates", f"{template_name}.html")
    base_html = read_file(template_path)

    html = str(mistune.html(md_text))
    page = base_html.replace("{{ title }}", title)
    page = page.replace("{{ content }}", html)

    return page

def read_file(filepath):
    with open(filepath, "r") as f:
        return f.read()

def write_file(filepath, content):
    with open(filepath, "w") as f:
        f.write(content)

if not os.path.exists("public"):
    os.makedirs("public")
else:
    shutil.rmtree("public")
    os.makedirs("public")

if not os.path.exists("templates"):
    os.makedirs("templates")
    with open(os.path.join("templates", "base.html"), "w") as f:
        f.write("""<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8">
        <title>{{ title }}</title>
    </head>
    <body>
        {{ content }}
    </body>
</html>""")

if not os.path.exists("static"):
    os.makedirs("static")

if not os.path.exists("content"):
    os.makedirs("content")
    with open(os.path.join("content", "index.md"), "w") as f:
        f.write("# Welcome to My Website\nThis is the homepage. Edit `content/index.md` to change this text.")

for filename in os.listdir("content"):
    if filename.endswith(".md"):
        md_text = read_file(os.path.join("content", filename))
        html_text = convert_md_to_html(md_text)
        output_filename = filename.replace(".md", ".html")
        write_file(os.path.join("public", output_filename), html_text)

shutil.copytree("static", os.path.join("public", "static"), dirs_exist_ok=True)