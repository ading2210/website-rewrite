import os
import markdown

from staticjinja import Site
from pathlib import Path

#template build script taken from the staticjinja documentation
#https://staticjinja.readthedocs.io/en/stable/user/advanced.html

def md_context(template):
  markdown_content = Path(template.filename).read_text()
  return {"post_content_html": markdowner.convert(markdown_content)}


def render_md(site, template, **kwargs):
  # i.e. posts/post1.md -> build/posts/post1.html
  out = site.outpath / Path(template.name).with_suffix(".html")

  # Compile and stream the result
  os.makedirs(out.parent, exist_ok=True)
  site.get_template("_post.html").stream(**kwargs).dump(str(out), encoding="utf-8")

site = Site.make_site(
  searchpath="src",
  outpath="output",
  contexts=[(r".*\.md", md_context)],
  rules=[(r".*\.md", render_md)],
)
site.render()