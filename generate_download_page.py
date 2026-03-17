"""
论文 PDF 批量下载 —— HTML 辅助页面生成器
=========================================
生成一个本地 HTML 文件，在你自己的浏览器里打开即可批量下载。
不涉及任何自动化工具，不会触发 Cloudflare。

使用:
    python generate_download_page.py

然后在 Chrome 中打开生成的 download_helper.html（确保在校园网/VPN 下）。
"""

import re
import os
import sys
import json

DOI_LIST_FILE = "checklist_2024_2026.txt" #可更改为目标DOI链接文本
OUTPUT_DIR    = "./downloaded_pdfs"


def parse_doi_list(filepath):
    entries = []
    year = "unknown"
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            m = re.match(r"【(\d{4})年】", line)
            if m:
                year = m.group(1)
                continue
            m = re.match(r"(\d+)\.\s*(https://doi\.org/.+)", line)
            if m:
                url = m.group(2).strip()
                doi = url.replace("https://doi.org/", "")
                pub = detect_publisher(doi)
                pdf_url = construct_pdf_url(doi, pub)
                entries.append({
                    "year": year,
                    "index": int(m.group(1)),
                    "doi": doi,
                    "doi_url": url,
                    "pdf_url": pdf_url if pdf_url else url,
                    "has_direct_pdf": pdf_url is not None,
                    "publisher": pub,
                })
    return entries


def detect_publisher(doi):
    if doi.startswith("10.1002/"): return "wiley"
    if doi.startswith("10.1021/"): return "acs"
    if doi.startswith("10.1016/"): return "elsevier"
    if doi.startswith("10.1038/"): return "nature"
    if doi.startswith("10.1126/"): return "science"
    return "unknown"


def construct_pdf_url(doi, publisher):
    if publisher == "wiley":
        return f"https://onlinelibrary.wiley.com/doi/pdfdirect/{doi}"
    elif publisher == "acs":
        return f"https://pubs.acs.org/doi/pdf/{doi}"
    elif publisher == "science":
        return f"https://www.science.org/doi/pdf/{doi}"
    return None


def generate_html(entries):
    papers_json = json.dumps(entries, ensure_ascii=False, indent=2)

    html = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>论文 PDF 批量下载助手</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
    font-family: -apple-system, 'Segoe UI', 'Microsoft YaHei', sans-serif;
    background: #0f0f1a; color: #e0e0e0; padding: 20px;
}
.container { max-width: 1200px; margin: 0 auto; }

h1 { color: #60a5fa; margin-bottom: 8px; font-size: 24px; }
.subtitle { color: #888; margin-bottom: 20px; }

/* 统计卡片 */
.stats {
    display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap;
}
.stat-card {
    background: #1a1a2e; border-radius: 8px; padding: 12px 20px;
    border-left: 3px solid #60a5fa; min-width: 120px;
}
.stat-card .num { font-size: 28px; font-weight: bold; color: #60a5fa; }
.stat-card .label { font-size: 12px; color: #888; }
.stat-card.success { border-color: #4ade80; }
.stat-card.success .num { color: #4ade80; }
.stat-card.fail { border-color: #f87171; }
.stat-card.fail .num { color: #f87171; }
.stat-card.pending { border-color: #fbbf24; }
.stat-card.pending .num { color: #fbbf24; }

/* 控制面板 */
.controls {
    background: #1a1a2e; border-radius: 8px; padding: 16px;
    margin-bottom: 20px;
}
.controls p { margin-bottom: 8px; line-height: 1.6; }
.controls .hint { color: #888; font-size: 13px; }

.btn-row { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px; }

button {
    padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer;
    font-size: 14px; font-weight: 500; transition: all 0.2s;
}
button:hover { transform: translateY(-1px); }
button:active { transform: translateY(0); }
.btn-primary { background: #3b82f6; color: white; }
.btn-primary:hover { background: #2563eb; }
.btn-success { background: #22c55e; color: white; }
.btn-success:hover { background: #16a34a; }
.btn-danger { background: #ef4444; color: white; }
.btn-danger:hover { background: #dc2626; }
.btn-secondary { background: #374151; color: #d1d5db; }
.btn-secondary:hover { background: #4b5563; }

select, input[type="number"] {
    background: #374151; color: white; border: 1px solid #555;
    border-radius: 4px; padding: 6px 10px; font-size: 14px;
}

#statusBar {
    margin-top: 12px; padding: 8px 12px; border-radius: 4px;
    background: #1e293b; font-size: 13px; min-height: 32px;
}

/* 进度条 */
.progress-bar {
    width: 100%; height: 6px; background: #374151; border-radius: 3px;
    margin-top: 8px; overflow: hidden;
}
.progress-fill {
    height: 100%; background: linear-gradient(90deg, #3b82f6, #22c55e);
    border-radius: 3px; transition: width 0.3s;
}

/* 表格 */
table { width: 100%; border-collapse: collapse; margin-top: 16px; }
th {
    background: #1a1a2e; padding: 10px 12px; text-align: left;
    font-size: 13px; color: #888; border-bottom: 2px solid #333;
    position: sticky; top: 0; z-index: 10;
}
td { padding: 8px 12px; border-bottom: 1px solid #1e1e30; font-size: 13px; }
tr:hover { background: #1a1a2e; }

a { color: #60a5fa; text-decoration: none; }
a:hover { text-decoration: underline; }

.tag {
    display: inline-block; padding: 2px 8px; border-radius: 4px;
    font-size: 11px; font-weight: 500;
}
.tag-wiley { background: #1e3a5f; color: #60a5fa; }
.tag-acs { background: #1e3a2f; color: #4ade80; }
.tag-elsevier { background: #3a2f1e; color: #fbbf24; }
.tag-nature { background: #3a1e2f; color: #f472b6; }
.tag-science { background: #2f1e3a; color: #a78bfa; }
.tag-unknown { background: #333; color: #999; }

.status-icon { font-size: 16px; }

/* 过滤器 */
.filters {
    display: flex; gap: 8px; align-items: center; margin-top: 12px;
    flex-wrap: wrap;
}
.filter-btn {
    padding: 4px 12px; border-radius: 12px; font-size: 12px;
    background: #374151; color: #d1d5db; border: none; cursor: pointer;
}
.filter-btn.active { background: #3b82f6; color: white; }
</style>
</head>
<body>
<div class="container">
    <h1>📄 论文 PDF 批量下载助手</h1>
    <p class="subtitle">在校园网 / VPN 环境下使用 · 支持 Wiley / ACS / Elsevier / Nature / Science</p>

    <div class="stats">
        <div class="stat-card"><div class="num" id="totalCount">0</div><div class="label">总计</div></div>
        <div class="stat-card success"><div class="num" id="openedCount">0</div><div class="label">已打开</div></div>
        <div class="stat-card pending"><div class="num" id="pendingCount">0</div><div class="label">待处理</div></div>
        <div class="stat-card fail"><div class="num" id="skippedCount">0</div><div class="label">跳过/失败</div></div>
    </div>

    <div class="controls">
        <p><strong>💡 使用方法：</strong></p>
        <p>1. 确保在<strong>校园网</strong>或已连接<strong>机构 VPN</strong></p>
        <p>2. 选择每批数量，点击「开始批量打开」</p>
        <p>3. 每隔几秒自动在新标签页打开一个 PDF 链接</p>
        <p>4. 浏览器会自动下载 PDF（或在新标签页显示 PDF，右键保存）</p>
        <p class="hint">⚠ 如果弹出验证码，手动完成后回来点「继续」。建议每批 5-10 篇，避免触发限速。</p>

        <div class="btn-row">
            <span style="line-height:32px;">每批:</span>
            <select id="batchSize">
                <option value="3">3 篇</option>
                <option value="5" selected>5 篇</option>
                <option value="10">10 篇</option>
                <option value="20">20 篇</option>
            </select>
            <span style="line-height:32px;">间隔:</span>
            <select id="interval">
                <option value="1500">1.5秒</option>
                <option value="2000">2秒</option>
                <option value="3000" selected>3秒</option>
                <option value="5000">5秒</option>
            </select>
            <button class="btn-primary" onclick="startBatch()">🚀 开始批量打开</button>
            <button class="btn-success" onclick="resumeBatch()">▶ 继续</button>
            <button class="btn-danger" onclick="stopBatch()">⏹ 暂停</button>
            <button class="btn-secondary" onclick="resetAll()">🔄 重置</button>
        </div>

        <div class="filters">
            <span style="font-size:12px;color:#888;">筛选:</span>
            <button class="filter-btn active" onclick="setFilter('all')">全部</button>
            <button class="filter-btn" onclick="setFilter('wiley')">Wiley</button>
            <button class="filter-btn" onclick="setFilter('acs')">ACS</button>
            <button class="filter-btn" onclick="setFilter('elsevier')">Elsevier</button>
            <button class="filter-btn" onclick="setFilter('nature')">Nature</button>
            <button class="filter-btn" onclick="setFilter('science')">Science</button>
            <button class="filter-btn" onclick="setFilter('pending')">⏳ 未打开</button>
        </div>

        <div id="statusBar">就绪，等待操作...</div>
        <div class="progress-bar"><div class="progress-fill" id="progressFill" style="width:0%"></div></div>
    </div>

    <table>
        <thead>
            <tr>
                <th style="width:50px">#</th>
                <th style="width:50px">年</th>
                <th>DOI</th>
                <th style="width:80px">出版商</th>
                <th style="width:100px">操作</th>
                <th style="width:60px">状态</th>
            </tr>
        </thead>
        <tbody id="tbody"></tbody>
    </table>
</div>

<script>
const papers = PAPERS_JSON_PLACEHOLDER;

// 状态: 'pending' | 'opened' | 'skipped'
const state = papers.map(() => 'pending');

// 从 localStorage 恢复进度
const saved = localStorage.getItem('paper_dl_state');
if (saved) {
    try {
        const arr = JSON.parse(saved);
        arr.forEach((s, i) => { if (i < state.length) state[i] = s; });
    } catch(e) {}
}

let currentIndex = state.findIndex(s => s === 'pending');
if (currentIndex === -1) currentIndex = papers.length;
let batchTimer = null;
let currentFilter = 'all';

function saveState() {
    localStorage.setItem('paper_dl_state', JSON.stringify(state));
}

function updateStats() {
    const total = papers.length;
    const opened = state.filter(s => s === 'opened').length;
    const skipped = state.filter(s => s === 'skipped').length;
    const pending = total - opened - skipped;

    document.getElementById('totalCount').textContent = total;
    document.getElementById('openedCount').textContent = opened;
    document.getElementById('pendingCount').textContent = pending;
    document.getElementById('skippedCount').textContent = skipped;

    const pct = ((opened + skipped) / total * 100).toFixed(1);
    document.getElementById('progressFill').style.width = pct + '%';
}

function setStatus(msg) {
    document.getElementById('statusBar').textContent = msg;
}

function render() {
    const tbody = document.getElementById('tbody');
    tbody.innerHTML = papers.map((p, i) => {
        // 过滤
        if (currentFilter === 'pending' && state[i] !== 'pending') return '';
        if (currentFilter !== 'all' && currentFilter !== 'pending' && p.publisher !== currentFilter) return '';

        const tagClass = `tag-${p.publisher}`;
        const statusIcon = state[i] === 'opened' ? '✅'
                         : state[i] === 'skipped' ? '⏭️' : '⏳';

        return `<tr id="row-${i}">
            <td>${p.year}-${String(p.index).padStart(3,'0')}</td>
            <td>${p.year}</td>
            <td>
                <a href="${p.doi_url}" target="_blank" title="${p.doi}">${p.doi}</a>
                ${!p.has_direct_pdf ? '<span style="color:#f87171;font-size:11px;"> (需手动)</span>' : ''}
            </td>
            <td><span class="tag ${tagClass}">${p.publisher}</span></td>
            <td>
                <a href="${p.pdf_url}" target="_blank" onclick="markOpened(${i})"
                   style="color:#4ade80;">📥 下载</a>
                &nbsp;
                <a href="#" onclick="markSkipped(${i});return false;"
                   style="color:#888;font-size:11px;">跳过</a>
            </td>
            <td class="status-icon">${statusIcon}</td>
        </tr>`;
    }).join('');

    updateStats();
}

function markOpened(i) {
    state[i] = 'opened';
    saveState();
    setTimeout(render, 100);
}

function markSkipped(i) {
    state[i] = 'skipped';
    saveState();
    render();
}

function findNextPending() {
    for (let i = 0; i < papers.length; i++) {
        if (state[i] === 'pending') return i;
    }
    return -1;
}

function openOne() {
    const i = findNextPending();
    if (i === -1) {
        stopBatch();
        setStatus('🎉 全部完成！');
        return false;
    }

    const p = papers[i];

    // 用隐藏的 <a> 标签模拟点击，绕过 popup blocker
    const a = document.createElement('a');
    a.href = p.pdf_url;
    a.target = '_blank';
    a.rel = 'noopener';
    a.style.display = 'none';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    markOpened(i);

    const opened = state.filter(s => s === 'opened').length;
    setStatus(`正在打开第 ${opened} 篇: ${p.doi}`);
    return true;
}

// 批量打开队列（用 setTimeout 链式调用代替 setInterval，更可靠）
let batchQueue = [];
let batchRunning = false;

function startBatch() {
    stopBatch();

    // 先测试弹窗是否被拦截
    const testWin = window.open('about:blank', '_blank');
    if (!testWin || testWin.closed) {
        setStatus('⚠️ 浏览器拦截了弹窗！请点击地址栏右侧的「允许弹窗」按钮，然后重试。');
        return;
    }
    testWin.close();

    const size = parseInt(document.getElementById('batchSize').value);
    const interval = parseInt(document.getElementById('interval').value);

    batchRunning = true;
    let count = 0;

    setStatus(`批量打开中... (每批 ${size} 篇，间隔 ${interval/1000}s)`);

    function next() {
        if (!batchRunning) return;
        if (count >= size || !openOne()) {
            batchRunning = false;
            const remaining = state.filter(s => s === 'pending').length;
            if (remaining > 0) {
                setStatus(`本批完成 (${count} 篇)。还剩 ${remaining} 篇，确认下载后点「继续」`);
            }
            return;
        }
        count++;
        setTimeout(next, interval);
    }

    next();
}

function resumeBatch() {
    startBatch();
}

function stopBatch() {
    batchRunning = false;
    if (batchTimer) {
        clearInterval(batchTimer);
        batchTimer = null;
    }
}

function resetAll() {
    if (!confirm('确认重置所有进度？')) return;
    state.fill('pending');
    saveState();
    currentIndex = 0;
    render();
    setStatus('已重置');
}

function setFilter(f) {
    currentFilter = f;
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.toggle('active', btn.textContent.toLowerCase().includes(f) ||
            (f === 'all' && btn.textContent === '全部') ||
            (f === 'pending' && btn.textContent.includes('未打开')));
    });
    render();
}

// 初始渲染
render();
</script>
</body>
</html>"""

    return html.replace("PAPERS_JSON_PLACEHOLDER", papers_json)


def main():
    entries = parse_doi_list(DOI_LIST_FILE)
    print(f"共解析 {len(entries)} 篇论文")

    # 统计出版商分布
    pubs = {}
    for e in entries:
        pubs[e["publisher"]] = pubs.get(e["publisher"], 0) + 1
    for p, c in sorted(pubs.items(), key=lambda x: -x[1]):
        direct = "✅ 可直接下载" if p in ("wiley", "acs", "science") else "⚠️ 需手动点击DOI页面"
        print(f"  {p}: {c} 篇  {direct}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    html = generate_html(entries)
    outpath = os.path.join(OUTPUT_DIR, "download_helper.html")
    with open(outpath, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n✅ 已生成: {outpath}")
    print(f"请在 Chrome 中打开此文件（确保在校园网/VPN 下）")

    if sys.platform == "win32":
        os.startfile(os.path.abspath(outpath))
        print("已自动在浏览器中打开！")


if __name__ == "__main__":
    main()
