import os
import shutil
import mistune
import json
import sys
from datetime import datetime

def read_config():
    if os.path.exists("config.json"):
        with open("config.json", "r") as f:
            return json.load(f)
    else:
        with open("config.json", "w", encoding="utf-8") as f:
            default_config = {
                "default_template": "base",
                "site_title": "My website",
                "site_url": "https://example.com",
                "site_description": "My personal website"
            }
            json.dump(default_config, f, indent=4)
            return default_config

def convert_md_to_html(md_text, filepath):
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
        try:
            parsed_metadata = json.loads(metadata)
        except json.JSONDecodeError as e:
            print(f"ERROR: JSON parse error in file '{filepath}': {e}")
            sys.exit(1)

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

    renderer = mistune.HTMLRenderer()
    markdown = mistune.Markdown(renderer=renderer, inline=mistune.InlineParser(False))
    html = str(markdown(md_text))
    page = base_html.replace("{{ title }}", title)
    page = page.replace("{{ content }}", html)

    return page, parsed_metadata, html, title

def read_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

def write_file(filepath, content):
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

def process_directory(content_dir, output_dir, blog_posts=None, pages_data=None):
    for item in os.listdir(content_dir):
        item_path = os.path.join(content_dir, item)
        
        if os.path.isdir(item_path):
            output_subdir = os.path.join(output_dir, item)
            os.makedirs(output_subdir, exist_ok=True)
            process_directory(item_path, output_subdir, blog_posts, pages_data)
        elif item.endswith(".md"):
            md_text = read_file(item_path)
            html_text, metadata, content_html, title = convert_md_to_html(md_text, item_path)
            output_filename = item.replace(".md", ".html")
            output_path = os.path.join(output_dir, output_filename)
            write_file(output_path, html_text)
            
            if pages_data is not None:
                relative_path = os.path.relpath(output_path, "public")
                route = "/" + relative_path.replace(".html", "").replace("index", "")
                if route == "/":
                    route = "/"
                elif route.endswith("/"):
                    route = route[:-1]
                
                pages_data[route] = {
                    "title": title,
                    "content": content_html
                }
            
            if blog_posts is not None and content_dir.endswith("blog"):
                relative_path = os.path.relpath(output_path, "public")
                blog_posts.append({
                    "path": relative_path,
                    "metadata": metadata,
                    "title": metadata.get("title", output_filename.replace(".html", ""))
                })

def generate_blog_page(blog_posts, pages_data=None):
    blog_posts.sort(key=lambda x: x["metadata"].get("date", ""), reverse=True)
    
    config = read_config()
    template_path = os.path.join("templates", "base.html")
    base_html = read_file(template_path)
    
    blog_html = "<h1>Blog Posts</h1>\n<ul>\n"
    for post in blog_posts:
        title = post["title"]
        path = post["path"]
        date = post["metadata"].get("date", "")
        
        route = "/" + path.replace(".html", "")
        
        if date:
            try:
                parsed_date = datetime.fromisoformat(date.replace("Z", "+00:00"))
                formatted_date = parsed_date.strftime("%B %d, %Y")
                blog_html += f'  <li><a href="{route}" data-spa-link>{title}</a> - {formatted_date}</li>\n'
            except:
                blog_html += f'  <li><a href="{route}" data-spa-link>{title}</a></li>\n'
        else:
            blog_html += f'  <li><a href="{route}" data-spa-link>{title}</a></li>\n'
    
    blog_html += "</ul>"
    
    page = base_html.replace("{{ title }}", f"Blog - {config['site_title']}")
    page = page.replace("{{ content }}", blog_html)
    
    write_file(os.path.join("public", "blog.html"), page)
    
    if pages_data is not None:
        pages_data["/blog"] = {
            "title": f"Blog - {config['site_title']}",
            "content": blog_html
        }

def generate_rss_feed(blog_posts):
    config = read_config()
    blog_posts.sort(key=lambda x: x["metadata"].get("date", ""), reverse=True)
    
    rss = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>{config['site_title']}</title>
    <link>{config['site_url']}</link>
    <description>{config['site_description']}</description>
    <language>en</language>
    <lastBuildDate>{datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')}</lastBuildDate>
"""
    
    for post in blog_posts:
        title = post["title"]
        path = post["path"]
        url = f"{config['site_url']}/{path}"
        date = post["metadata"].get("date", "")
        description = post["metadata"].get("description", title)
        
        if date:
            try:
                parsed_date = datetime.fromisoformat(date.replace("Z", "+00:00"))
                rfc822_date = parsed_date.strftime('%a, %d %b %Y %H:%M:%S %z')
            except:
                rfc822_date = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
        else:
            rfc822_date = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
        
        rss += f"""
    <item>
      <title>{title}</title>
      <link>{url}</link>
      <description>{description}</description>
      <pubDate>{rfc822_date}</pubDate>
      <guid>{url}</guid>
    </item>"""
    
    rss += """
  </channel>
</rss>"""
    
    write_file(os.path.join("public", "rss.xml"), rss)

def generate_spa_data(pages_data):
    spa_js = f"""
// SPA Router and Page Data
const PAGES_DATA = {json.dumps(pages_data, indent=2)};

class SPARouter {{
    constructor() {{
        this.currentPath = window.location.pathname;
        this.init();
    }}

    init() {{
        // Handle initial page load
        this.loadPage(this.currentPath);
        
        // Handle browser back/forward buttons
        window.addEventListener('popstate', (e) => {{
            this.loadPage(window.location.pathname, false);
        }});
        
        // Handle SPA link clicks
        document.addEventListener('click', (e) => {{
            const link = e.target.closest('a[data-spa-link]');
            if (link) {{
                e.preventDefault();
                const href = link.getAttribute('href');
                this.navigateTo(href);
            }}
        }});
        
        // Convert regular internal links to SPA links
        this.convertInternalLinks();
    }}

    convertInternalLinks() {{
        const links = document.querySelectorAll('a:not([data-spa-link]):not([href^="http"]):not([href^="#"]):not([href^="mailto"]):not([href^="tel"])');
        links.forEach(link => {{
            const href = link.getAttribute('href');
            if (href && !href.includes('.xml') && !href.includes('.txt') && !href.includes('.gif') && !href.includes('.jpg') && !href.includes('.png')) {{
                link.setAttribute('data-spa-link', '');
            }}
        }});
    }}

    navigateTo(path) {{
        if (path === this.currentPath) return;
        
        history.pushState(null, '', path);
        this.loadPage(path, true);
    }}

    loadPage(path, updateHistory = false) {{
        // Normalize path
        let normalizedPath = path;
        if (normalizedPath === '' || normalizedPath === '/') {{
            normalizedPath = '/';
        }} else if (normalizedPath.endsWith('/')) {{
            normalizedPath = normalizedPath.slice(0, -1);
        }}
        
        // Remove .html extension from path for lookup
        if (normalizedPath.endsWith('.html')) {{
            normalizedPath = normalizedPath.replace('.html', '');
        }}
        if (normalizedPath === '') {{
            normalizedPath = '/';
        }}
        
        // Check if page exists in our data
        let pageData = PAGES_DATA[normalizedPath];
        
        // Fallback for index pages
        if (!pageData && normalizedPath === '/') {{
            pageData = PAGES_DATA['/'] || PAGES_DATA['/index'];
        }}
        
        if (pageData) {{
            document.title = pageData.title;
            
            // Find the main content container
            const mainContentContainer = document.querySelector('.main-content');
            if (!mainContentContainer) {{
                console.error('Main content container not found');
                return;
            }}
            
            // Update the window title attribute
            mainContentContainer.setAttribute('data-window-title', pageData.title);
            
            // Simple fade effect
            mainContentContainer.style.opacity = '0.7';
            
            setTimeout(() => {{
                // Find the content area (everything after window controls)
                const windowControls = mainContentContainer.querySelector('.window-controls');
                
                // Clear existing content but preserve window controls
                const children = Array.from(mainContentContainer.children);
                children.forEach(child => {{
                    if (!child.classList.contains('window-controls')) {{
                        child.remove();
                    }}
                }});
                
                // Add new content
                const contentDiv = document.createElement('div');
                contentDiv.innerHTML = pageData.content;
                mainContentContainer.appendChild(contentDiv);
                
                mainContentContainer.style.opacity = '1';
                
                // Re-initialize SPA links for new content
                this.convertInternalLinks();
                
                // Scroll to top
                window.scrollTo(0, 0);
            }}, 100);
            
            this.currentPath = normalizedPath;
        }} else {{
            // Page not found in SPA data, do regular navigation
            window.location.href = path;
        }}
    }}
}}

// Initialize SPA when DOM is ready
if (document.readyState === 'loading') {{
    document.addEventListener('DOMContentLoaded', () => {{
        new SPARouter();
    }});
}} else {{
    new SPARouter();
}}
"""
    
    write_file(os.path.join("public", "spa.js"), spa_js)

def create_post(title):
    if not os.path.exists(os.path.join("content", "blog")):
        os.makedirs(os.path.join("content", "blog"))
    
    slug = title.lower().replace(" ", "_").replace("'", "").replace('"', "")
    slug = "".join(c for c in slug if c.isalnum() or c == "_")
    current_date = datetime.now().isoformat()
    
    filename = f"{slug}.md"
    filepath = os.path.join("content", "blog", filename)
    
    if os.path.exists(filepath):
        print(f"ERROR: Post '{filename}' already exists!")
        sys.exit(1)
    
    post_content = """{
    "title": "%s",
    "date": "%s"
}
===

# %s

Write your post content here...
""" % (title, current_date, title)
    
    write_file(filepath, post_content)
    print(f"Created new post: {filepath}")

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "post" and len(sys.argv) > 2:
            title = " ".join(sys.argv[2:])
            create_post(title)
            return
        else:
            print("Usage: python main.py [post <title>]")
            return

    if not os.path.exists("public"):
        os.makedirs("public")
    else:
        shutil.rmtree("public")
        os.makedirs("public")

    if not os.path.exists("templates"):
        os.makedirs("templates")
        with open(os.path.join("templates", "base.html"), "w", encoding="utf-8") as f:
            f.write("""<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8">
        <title>{{ title }}</title>
        <style>
            body {
                transition: opacity 0.2s ease-in-out;
            }
        </style>
    </head>
    <body>
        {{ content }}
        <script src="/spa.js"></script>
    </body>
</html>""")

    if not os.path.exists("static"):
        os.makedirs("static")

    if not os.path.exists("content"):
        os.makedirs("content")
        with open(os.path.join("content", "index.md"), "w", encoding="utf-8") as f:
            f.write("# Welcome to My Website\nThis is the homepage. Edit `content/index.md` to change this text.")

    blog_posts = []
    pages_data = {}
    has_blog_dir = os.path.exists(os.path.join("content", "blog"))

    process_directory("content", "public", blog_posts if has_blog_dir else None, pages_data)

    if has_blog_dir and blog_posts:
        generate_blog_page(blog_posts, pages_data)
        generate_rss_feed(blog_posts)

    generate_spa_data(pages_data)

    shutil.copytree("static", "public", dirs_exist_ok=True)
    
    print("Site generated successfully!")

if __name__ == "__main__":
    main()