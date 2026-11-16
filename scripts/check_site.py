#!/usr/bin/env python3
"""檢查網站是否符合 CLAUDE.md 的規則。只用標準函式庫。

用法（在專案根目錄）：python3 scripts/check_site.py
全部通過會印 CHECK ALL OK 並以 0 結束；有問題會列出每一條並以 1 結束。
"""
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUFFIX = " · 居家滅蚊遊戲筆記"
ALLOWED_TAGS = {"confirmed", "proposed", "measured", "example"}
errors = []


def err(path, msg):
    errors.append(f"{path.relative_to(ROOT)}: {msg}")


class Scan(HTMLParser):
    def __init__(self):
        super().__init__()
        self.h1 = 0
        self.title = ""
        self._in_title = False
        self.meta_desc = False
        self.viewport = False
        self.charset = False
        self.lang = None
        self.body_attrs = {}
        self.refs = []          # (attr, value)
        self.tag_classes = set()
        self.inline_style = False
        self.ids = set()
        self.scripts = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html":
            self.lang = a.get("lang")
        if tag == "h1":
            self.h1 += 1
        if tag == "title":
            self._in_title = True
        if tag == "meta":
            if a.get("name") == "description" and a.get("content"):
                self.meta_desc = True
            if a.get("name") == "viewport":
                self.viewport = True
            if a.get("charset"):
                self.charset = True
        if tag == "body":
            self.body_attrs = a
        if tag == "style":
            self.inline_style = True
        if "style" in a:
            self.inline_style = True
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "script" and a.get("src"):
            self.scripts.append(a["src"])
        for key in ("href", "src"):
            if key in a and a[key]:
                self.refs.append(a[key])
        if tag == "span" and "class" in a:
            cls = a["class"].split()
            if "tag" in cls:
                self.tag_classes.update(c for c in cls if c != "tag")

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def registered_pages():
    text = (ROOT / "assets" / "pages-data.js").read_text(encoding="utf-8")
    return re.findall(r'file:\s*"([^"]+)"', text)


def main():
    registered = registered_pages()
    actual = sorted(str(p.relative_to(ROOT)) for p in (ROOT / "pages").glob("*.html"))
    for f in registered:
        if not (ROOT / f).exists():
            errors.append(f"pages-data.js 登記了 {f}，但檔案不存在")
    for f in actual:
        if f not in registered:
            errors.append(f"{f} 沒有登記在 assets/pages-data.js")
    if len(set(registered)) != len(registered):
        errors.append("pages-data.js 有重複登記的頁面")

    html_files = [ROOT / "index.html"] + [ROOT / f for f in actual]
    for path in html_files:
        rel = str(path.relative_to(ROOT))
        text = path.read_text(encoding="utf-8")
        s = Scan()
        s.feed(text)
        is_index = rel == "index.html"
        if s.lang != "zh-Hant":
            err(path, '<html> 必須有 lang="zh-Hant"')
        if not s.charset:
            err(path, "缺少 <meta charset>")
        if not s.viewport:
            err(path, "缺少 viewport meta")
        if not s.meta_desc:
            err(path, "缺少 meta description")
        if s.h1 != 1:
            err(path, f"必須剛好一個 <h1>，目前 {s.h1} 個")
        if not is_index and not s.title.endswith(SUFFIX):
            err(path, f"<title> 必須以「{SUFFIX}」結尾")
        if s.inline_style:
            err(path, "不可使用 inline style 或 <style>，樣式放 assets/site.css")
        if re.search(r"#[0-9a-fA-F]{3,8}\b", re.sub(r"&#\d+;", "", text)):
            err(path, "頁面內不可寫死色碼，請用 CSS token")
        expected_root = "" if is_index else "../"
        if s.body_attrs.get("data-root") != expected_root:
            err(path, f'body data-root 應為 "{expected_root}"')
        if s.body_attrs.get("data-page") != rel:
            err(path, f'body data-page 應為 "{rel}"')
        if "site-header" not in s.ids or "site-footer" not in s.ids:
            err(path, "缺少 #site-header 或 #site-footer")
        if not is_index and "pager" not in s.ids:
            err(path, "缺少 #pager")
        if not is_index and "資料來源" not in text:
            err(path, '缺少 <p class="meta"> 的「資料來源」說明')
        for cls in s.tag_classes - ALLOWED_TAGS:
            err(path, f"未知的標記 class「tag {cls}」，只允許 {sorted(ALLOWED_TAGS)}")
        for ref in s.refs:
            if re.match(r"^(https?:|mailto:|#)", ref):
                continue
            target = (path.parent / ref.split("#")[0]).resolve()
            if not target.exists():
                err(path, f"連結或資源不存在：{ref}")

    if errors:
        print("CHECK FAILED")
        for e in errors:
            print(" -", e)
        sys.exit(1)
    print(f"CHECK ALL OK（{len(html_files)} 個頁面）")


if __name__ == "__main__":
    main()
