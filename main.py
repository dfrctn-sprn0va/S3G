import os
import shutil
import mistune
import json
from datetime import datetime

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

    parsed_metadata = {}
    if metadata:
        parsed_metadata = json.loads(metadata)

        if "template" in parsed_metadata:
            template_name = parsed_metadata["template"]
        else:
            template_name = "base"
        
        if "title" in parsed_metadata:
            title = parsed_metadata["title"]
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

    return page, parsed_metadata

def read_file(filepath):
    with open(filepath, "r") as f:
        return f.read()

def write_file(filepath, content):
    with open(filepath, "w") as f:
        f.write(content)

def process_directory(content_dir, output_dir, blog_posts=None):
    for item in os.listdir(content_dir):
        item_path = os.path.join(content_dir, item)
        
        if os.path.isdir(item_path):
            output_subdir = os.path.join(output_dir, item)
            os.makedirs(output_subdir, exist_ok=True)
            process_directory(item_path, output_subdir, blog_posts)
        elif item.endswith(".md"):
            md_text = read_file(item_path)
            html_text, metadata = convert_md_to_html(md_text)
            output_filename = item.replace(".md", ".html")
            output_path = os.path.join(output_dir, output_filename)
            write_file(output_path, html_text)
            
            if blog_posts is not None and content_dir.endswith("blog"):
                relative_path = os.path.relpath(output_path, "public")
                blog_posts.append({
                    "path": relative_path,
                    "metadata": metadata,
                    "title": metadata.get("title", output_filename.replace(".html", ""))
                })

def generate_blog_page(blog_posts):
    blog_posts.sort(key=lambda x: x["metadata"].get("date", ""), reverse=True)
    
    config = read_config()
    template_path = os.path.join("templates", "base.html")
    base_html = read_file(template_path)
    
    blog_html = "<h1>Blog Posts</h1>\n<ul>\n"
    for post in blog_posts:
        title = post["title"]
        path = post["path"]
        date = post["metadata"].get("date", "")
        
        if date:
            try:
                parsed_date = datetime.fromisoformat(date.replace("Z", "+00:00"))
                formatted_date = parsed_date.strftime("%B %d, %Y")
                blog_html += f'  <li><a href="{path}">{title}</a> - {formatted_date}</li>\n'
            except:
                blog_html += f'  <li><a href="{path}">{title}</a></li>\n'
        else:
            blog_html += f'  <li><a href="{path}">{title}</a></li>\n'
    
    blog_html += "</ul>"
    
    page = base_html.replace("{{ title }}", f"Blog - {config['site_title']}")
    page = page.replace("{{ content }}", blog_html)
    
    write_file(os.path.join("public", "blog.html"), page)

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

blog_posts = []
has_blog_dir = os.path.exists(os.path.join("content", "blog"))

process_directory("content", "public", blog_posts if has_blog_dir else None)

if has_blog_dir and blog_posts:
    generate_blog_page(blog_posts)

shutil.copytree("static", "public", dirs_exist_ok=True)