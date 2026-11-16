// 全站頁面清單 —— 唯一的資料來源（導覽列、首頁卡片、上一頁／下一頁都由它產生）。
// 新增頁面時：在這裡加一筆，順序就是導覽順序。欄位說明見 CLAUDE.md「新增頁面流程」。
window.SITE_PAGES = [
  { file: "pages/game-overview.html",     title: "遊戲總覽",     summary: "這是一款什麼遊戲、核心循環是什麼、哪些是已確認的方向。" },
  { file: "pages/mosquito-behavior.html", title: "蚊子行為",     summary: "蚊子的狀態機、聲音線索，以及目前的試玩初始數值。" },
  { file: "pages/milestones.html",        title: "里程碑進度",   summary: "M1 到 M5 各自完成了什麼、驗證到哪裡、還沒驗證什麼。" },
  { file: "pages/design-decisions.html",  title: "設計決策",     summary: "哪些是使用者已確認的決策，哪些只是建議，以及為什麼這樣分。" },
  { file: "pages/ai-assistant.html",      title: "AI 研究助手",  summary: "助手的角色、不能做的事，以及目前暫停的原因與狀態。" }
];
