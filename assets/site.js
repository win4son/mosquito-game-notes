// 共用腳本：依 assets/pages-data.js 產生導覽列、首頁卡片、上一頁／下一頁、頁尾。
// 頁面只需在 <body> 設定 data-root（根目錄頁用 ""，pages/ 內的頁面用 "../"）。
(function () {
  var body = document.body;
  var root = body.getAttribute("data-root") || "";
  var pages = window.SITE_PAGES || [];
  var current = body.getAttribute("data-page") || "";

  // 導覽列
  var header = document.getElementById("site-header");
  if (header) {
    var links = pages.map(function (p) {
      var cur = p.file === current ? ' aria-current="page"' : "";
      return '<a href="' + root + p.file + '"' + cur + ">" + p.title + "</a>";
    }).join("");
    header.className = "site-header";
    header.innerHTML =
      '<div class="inner"><a class="brand" href="' + root + 'index.html">🦟 居家滅蚊遊戲筆記</a>' +
      '<nav class="site-nav" aria-label="主選單">' + links + "</nav></div>";
  }

  // 首頁卡片
  var cards = document.getElementById("page-cards");
  if (cards) {
    cards.innerHTML = pages.map(function (p) {
      return '<a class="card" href="' + root + p.file + '"><h3>' + p.title + "</h3><p>" + p.summary + "</p></a>";
    }).join("");
  }

  // 上一頁／下一頁
  var pager = document.getElementById("pager");
  if (pager) {
    var i = pages.findIndex(function (p) { return p.file === current; });
    var html = "";
    if (i > 0) html += '<a href="' + root + pages[i - 1].file + '">← ' + pages[i - 1].title + "</a>";
    else html += "<span></span>";
    if (i >= 0 && i < pages.length - 1) html += '<a href="' + root + pages[i + 1].file + '">' + pages[i + 1].title + " →</a>";
    pager.className = "pager";
    pager.innerHTML = html;
  }

  // 頁尾
  var footer = document.getElementById("site-footer");
  if (footer) {
    footer.className = "site-footer";
    footer.innerHTML =
      "國立暨南國際大學「生成式 AI」期末專案 · 學生：李志恒<br>" +
      "本站是階段性企劃加原型的紀錄，不是完成品。試玩回饋目前只有開發者一人。";
  }
})();
