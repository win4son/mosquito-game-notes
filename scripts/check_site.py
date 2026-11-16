#!/usr/bin/env python3
"""檢查網站是否符合 CLAUDE.md 的規則。只用標準函式庫。

用法（在專案根目錄）：python3 scripts/check_site.py
全部通過會印 CHECK ALL OK 並以 0 結束；有問題會列出每一條並以 1 結束。

檢查範圍（對應 CLAUDE.md 第 11 節）：
  - 頁面登記、連結與資源路徑
  - <title>／lang／meta／<h1>、body 屬性、固定骨架
  - 禁用 inline style 與色碼；標記 class 只限五種
  - meta「資料來源」每個檔名後面都有章節
  - <li>、<tbody> 的表格列、含數值單位的 <p>：自己或所屬標題要有標記

不檢查：標記選得對不對、內容與上層規格是否一致、章節是否真的存在、畫面版面。
所以 CHECK ALL OK 不等於完全符合 CLAUDE.md。
"""
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUFFIX = " · 居家滅蚊遊戲筆記"
ALLOWED_TAGS = {"confirmed", "proposed", "measured", "example", "pending"}
NUMERIC = re.compile(r"\d+(\.\d+)?\s*(m|秒|%|項|隻|次|個)")
# 檔名後面必須接「第 N 節」（可含 ～、頓號、小數點）或「章節名稱」
CHAPTER = re.compile(r"^\s*(第\s*[\d.、～,，\s]+節|「[^」]+」)")
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
        self.refs = []
        self.tag_classes = set()
        self.inline_style = False
        self.ids = set()
        self.in_main = False
        self.in_thead = False
        self.blocks = []         # 目前開啟中的 li／tr／p：dict(kind, text, has_tag, exempt)
        self.heading = None      # 目前開啟中的標題：dict(level, has_tag)
        self.h2_tag = False
        self.h3_tag = False
        self.problems = []       # (kind, 摘要)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = a.get("class", "").split()
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
        if tag == "style" or "style" in a:
            self.inline_style = True
        if "id" in a:
            self.ids.add(a["id"])
        for key in ("href", "src"):
            if key in a and a[key]:
                self.refs.append(a[key])
        if tag == "main":
            self.in_main = True
        if tag == "thead":
            self.in_thead = True
        if self.in_main:
            if tag in ("h2", "h3"):
                self.heading = {"level": tag, "has_tag": False}
                if tag == "h2":
                    self.h3_tag = False
            if tag == "li":
                self.blocks.append({"kind": "li", "text": "", "has_tag": False, "exempt": False})
            elif tag == "tr" and not self.in_thead:
                self.blocks.append({"kind": "表格列", "text": "", "has_tag": False, "exempt": False})
            elif tag == "p":
                exempt = "lead" in cls or "meta" in cls
                self.blocks.append({"kind": "p", "text": "", "has_tag": False, "exempt": exempt})
        if tag == "span" and "tag" in cls:
            self.tag_classes.update(c for c in cls if c != "tag")
            for b in self.blocks:
                b["has_tag"] = True
            if self.heading:
                self.heading["has_tag"] = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag == "main":
            self.in_main = False
        if tag == "thead":
            self.in_thead = False
        if tag in ("h2", "h3") and self.heading and self.heading["level"] == tag:
            if tag == "h2":
                self.h2_tag = self.heading["has_tag"]
            else:
                self.h3_tag = self.heading["has_tag"]
            self.heading = None
        kind = {"li": "li", "tr": "表格列", "p": "p"}.get(tag)
        if kind and self.blocks and self.blocks[-1]["kind"] == kind:
            b = self.blocks.pop()
            covered = b["has_tag"] or self.h2_tag or self.h3_tag
            text = re.sub(r"\s+", " ", b["text"]).strip()
            if b["exempt"] or covered:
                return
            if kind in ("li", "表格列") or NUMERIC.search(text):
                self.problems.append((kind, text[:30]))

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        for b in self.blocks:
            b["text"] += data


def registered_pages():
    text = (ROOT / "assets" / "pages-data.js").read_text(encoding="utf-8")
    return re.findall(r'file:\s*"([^"]+)"', text)


def check_meta_sources(path, text):
    m = re.search(r'<p class="meta">(.*?)</p>', text, re.S)
    if not m:
        err(path, '缺少 <p class="meta">')
        return
    meta = m.group(1)
    if "資料來源" not in meta:
        err(path, 'meta 缺少「資料來源」')
        return
    # 只看「最後核對」之前的部分
    src = meta.split("最後核對")[0]
    if "*" in src:
        err(path, "資料來源不可用 M*_Spec.md 這種統稱，要列出每個檔案")
    codes = list(re.finditer(r"<code>([^<]+)</code>", src))
    if not codes:
        err(path, "資料來源沒有任何 <code>檔名</code>")
    for c in codes:
        rest = src[c.end():]
        if not CHAPTER.match(rest):
            err(path, f"資料來源「{c.group(1)}」後面缺少章節（第 N 節 或「章節名稱」）")


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
        if not is_index:
            if "pager" not in s.ids:
                err(path, "缺少 #pager")
            check_meta_sources(path, text)
        for cls in s.tag_classes - ALLOWED_TAGS:
            err(path, f"未知的標記 class「tag {cls}」，只允許 {sorted(ALLOWED_TAGS)}")
        for kind, snippet in s.problems:
            err(path, f"{kind}沒有標記（自己與所屬標題都沒有）：「{snippet}…」")
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
