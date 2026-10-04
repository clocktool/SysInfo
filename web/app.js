async function loadAll() {
    document.getElementById("loading").classList.remove("hidden");
    document.getElementById("report").classList.add("hidden");

    try {
        const r = await fetch("/api/all");
        const data = await r.json();
        const browserInfo = await collectBrowserInfo();
        data.browser = browserInfo;

        render(data);
        document.getElementById("loading").classList.add("hidden");
        document.getElementById("report").classList.remove("hidden");
    } catch (e) {
        document.getElementById("loading").innerHTML =
            `<i class="fas fa-triangle-exclamation"></i> 加载失败: ${e}`;
    }
}

/* ============ 渲染 ============ */
function render(data) {
    const el = document.getElementById("report");
    el.innerHTML = "";

    // 1. 系统信息
    el.appendChild(section("fa-computer", "系统信息", [
        item("fa-windows", "操作系统", data.system.os),
        item("fa-server", "主机名", data.system.hostname),
        item("fa-microchip", "架构", data.system.machine),
        item("fa-brain", "CPU", data.system.processor),
        item("fa-layer-group", "核心",
            `${data.system.cpu_logical} 逻辑 / ${data.system.cpu_physical} 物理`),
        item("fa-memory", "内存",
            `${data.system.ram_used_gb} / ${data.system.ram_total_gb} GB (${data.system.ram_percent}%)`),
        item("fa-python", "Python", data.system.python_version),
        item("fa-clock", "启动时间", data.system.boot_time),
    ]));

    // 2. 硬件
    const hw = [];
    data.system.disks.forEach(d => {
        hw.push(item("fa-hard-drive",
            `${d.mount} 磁盘`,
            `${d.used_gb} / ${d.total_gb} GB <span class="note">${d.fstype} · ${d.percent}% 已用</span>`));
    });
    if (data.system.battery) {
        const b = data.system.battery;
        hw.push(item("fa-bolt", "电池电量", `${b.percent}%`));
        hw.push(item("fa-plug", "电池状态", b.plugged ? "充电中" : "使用中"));
    }
    if (hw.length) el.appendChild(section("fa-microchip", "硬件", hw));

    // 3. 网络地址
    el.appendChild(section("fa-network-wired", "网络地址", [
        item("fa-globe", "公网 IPv4",
            data.network.public_ipv4
                ? `<span class="tag public">${data.network.public_ipv4}</span>`
                : '<span class="empty">无</span>'),
        item("fa-globe", "公网 IPv6",
            data.network.public_ipv6
                ? `<span class="tag public">${truncate(data.network.public_ipv6, 32)}</span>`
                : '<span class="empty">无</span>'),
        item("fa-house", "本地 IPv4",
            data.network.local_ips.ipv4.length
                ? data.network.local_ips.ipv4
                    .map(x => `<div><span class="tag">${x.addr}</span> <span class="note">${x.iface}</span></div>`)
                    .join("")
                : '<span class="empty">无</span>'),
        item("fa-house", "本地 IPv6",
            data.network.local_ips.ipv6.length
                ? data.network.local_ips.ipv6
                    .map(x => `<div><span class="tag">${x.addr}</span> <span class="note">${x.iface}</span></div>`)
                    .join("")
                : '<span class="empty">无</span>'),
        item("fa-ethernet", "MAC 地址",
            data.network.mac
                ? `<span class="tag">${data.network.mac}</span>`
                : '<span class="empty">未知</span>'),
        item("fa-door-open", "网关",
            data.network.gateway
                ? `<span class="tag">${data.network.gateway}</span>`
                : '<span class="empty">未知</span>'),
        item("fa-server", "DNS",
            data.network.dns_servers.length
                ? data.network.dns_servers.map(d => `<span class="tag">${d}</span>`).join("")
                : '<span class="empty">未知</span>'),
    ]));

    // 4. IP 地理位置
    if (data.geo && data.geo.country) {
        el.appendChild(section("fa-location-dot", "IP 地理位置", [
            item("fa-flag", "国家 / 地区",
                `${data.geo.country}${data.geo.countryCode ? ` (${data.geo.countryCode})` : ""}`),
            item("fa-map", "地区", data.geo.regionName),
            item("fa-city", "城市", data.geo.city),
            item("fa-envelope", "邮编", data.geo.zip || "—"),
            item("fa-crosshairs", "纬度 / 经度", `${data.geo.lat}, ${data.geo.lon}`),
            item("fa-clock", "时区", data.geo.timezone),
            item("fa-building", "ISP", data.geo.isp),
            item("fa-sitemap", "组织", data.geo.org),
            item("fa-network-wired", "AS", data.geo.as),
        ]));
    }

    // 5. 浏览器 / 设备
    el.appendChild(section("fa-window-maximize", "浏览器 / 设备", [
        item("fa-fingerprint", "User-Agent", data.browser.userAgent),
        item("fa-desktop", "平台", data.browser.platform),
        item("fa-language", "语言", data.browser.language),
        item("fa-clock", "时区", data.browser.timezone),
        item("fa-display", "屏幕", data.browser.screen),
        item("fa-magnifying-glass", "像素比", data.browser.devicePixelRatio),
        item("fa-microchip", "CPU 核心", data.browser.cpuCores),
        item("fa-memory", "设备内存",
            data.browser.deviceMemory ? `${data.browser.deviceMemory} GB` : "未知"),
        item("fa-hand-pointer", "触控",
            data.browser.touchSupport ? "支持" : "不支持"),
        item("fa-cookie-bite", "Cookie",
            data.browser.cookiesEnabled ? "启用" : "禁用"),
        item("fa-user-shield", "DNT", data.browser.doNotTrack),
    ]));

    // 6. 浏览器指纹
    el.appendChild(section("fa-fingerprint", "浏览器指纹", [
        item("fa-palette", "Canvas 指纹",
            `<span class="tag hash">${data.browser.canvasFp}</span>`),
        item("fa-cube", "WebGL 供应商", data.browser.webglVendor),
        item("fa-cube", "WebGL 渲染器", data.browser.webglRenderer),
        item("fa-music", "音频指纹",
            `<span class="tag hash">${data.browser.audioFp}</span>`),
        item("fa-font", "字体数量", `${data.browser.fontsCount} 种`),
    ]));
}

/* ============ 构建工具 ============ */
function section(icon, title, items) {
    const s = document.createElement("div");
    s.className = "section";
    s.innerHTML = `
        <div class="section-title">
            <i class="fas ${icon}"></i>
            <span>${title}</span>
            <span class="count">(${items.length})</span>
        </div>
        <div class="grid"></div>
    `;
    const grid = s.querySelector(".grid");
    items.forEach(it => grid.appendChild(it));
    return s;
}

function item(icon, label, valueHtml) {
    const i = document.createElement("div");
    i.className = "item";

    // 复制用的纯文本：把 html 标签去掉，保留可读文字
    const plain = stripHtml(valueHtml);

    i.innerHTML = `
        <div class="item-label">
            <i class="fas ${icon}"></i>
            <span>${label}</span>
        </div>
        <div class="item-value">${valueHtml}</div>
        <button class="copy-btn" title="复制"><i class="fas fa-copy"></i></button>
    `;

    const btn = i.querySelector(".copy-btn");
    btn.addEventListener("click", (e) => {
        e.stopPropagation();
        copyToClipboard(plain).then(() => {
            btn.classList.add("copied");
            btn.innerHTML = '<i class="fas fa-check"></i>';
            setTimeout(() => {
                btn.classList.remove("copied");
                btn.innerHTML = '<i class="fas fa-copy"></i>';
            }, 1200);
        });
    });

    return i;
}

function stripHtml(html) {
    const tmp = document.createElement("div");
    tmp.innerHTML = html;
    return tmp.textContent || tmp.innerText || "";
}

function truncate(s, n) {
    return s.length > n ? s.slice(0, n) + "…" : s;
}

async function copyToClipboard(text) {
    try {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            await navigator.clipboard.writeText(text);
            return;
        }
    } catch (e) {}
    // fallback
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.style.position = "fixed";
    ta.style.left = "-9999px";
    document.body.appendChild(ta);
    ta.select();
    document.execCommand("copy");
    document.body.removeChild(ta);
}

/* ============ 浏览器端采集（不变） ============ */
async function collectBrowserInfo() {
    const info = {
        userAgent: navigator.userAgent,
        platform: navigator.platform,
        language: navigator.language,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        screen: `${screen.width} × ${screen.height}`,
        devicePixelRatio: window.devicePixelRatio,
        cpuCores: navigator.hardwareConcurrency || "未知",
        deviceMemory: navigator.deviceMemory || null,
        touchSupport: "ontouchstart" in window,
        cookiesEnabled: navigator.cookieEnabled,
        doNotTrack: navigator.doNotTrack || "未设置",
        canvasFp: canvasFingerprint(),
        webglVendor: "",
        webglRenderer: "",
        audioFp: "",
        fontsCount: 0,
    };

    try {
        const canvas = document.createElement("canvas");
        const gl = canvas.getContext("webgl") || canvas.getContext("experimental-webgl");
        if (gl) {
            const dbg = gl.getExtension("WEBGL_debug_renderer_info");
            if (dbg) {
                info.webglVendor = gl.getParameter(dbg.UNMASKED_VENDOR_WEBGL);
                info.webglRenderer = gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL);
            }
        }
    } catch (e) {}

    try { info.audioFp = await audioFingerprint(); } catch (e) {}
    info.fontsCount = detectFonts();
    return info;
}

function canvasFingerprint() {
    try {
        const canvas = document.createElement("canvas");
        canvas.width = 200; canvas.height = 40;
        const ctx = canvas.getContext("2d");
        ctx.textBaseline = "top";
        ctx.font = "14px 'Arial'";
        ctx.fillStyle = "#f60";
        ctx.fillRect(0, 0, 200, 40);
        ctx.fillStyle = "#069";
        ctx.fillText("设备信息查询器-指纹测试", 2, 15);
        ctx.fillStyle = "rgba(102, 204, 0, 0.7)";
        ctx.fillText("设备信息查询器-指纹测试", 4, 17);
        const data = canvas.toDataURL();
        let hash = 0;
        for (let i = 0; i < data.length; i++) {
            hash = ((hash << 5) - hash + data.charCodeAt(i)) | 0;
        }
        return Math.abs(hash).toString(16).padStart(8, "0");
    } catch (e) { return "不支持"; }
}

async function audioFingerprint() {
    try {
        const ctx = new (window.OfflineAudioContext || window.webkitOfflineAudioContext)(1, 44100, 44100);
        const osc = ctx.createOscillator();
        osc.type = "triangle";
        osc.frequency.value = 10000;
        const comp = ctx.createDynamicsCompressor();
        osc.connect(comp);
        comp.connect(ctx.destination);
        osc.start(0);
        const buffer = await ctx.startRendering();
        const data = buffer.getChannelData(0);
        let sum = 0;
        for (let i = 0; i < data.length; i++) sum += Math.abs(data[i]);
        return sum.toString(16).slice(0, 12);
    } catch (e) { return "不支持"; }
}

function detectFonts() {
    const fonts = [
        "Arial", "Verdana", "Times New Roman", "Courier New",
        "Microsoft YaHei", "SimSun", "SimHei", "KaiTi",
        "Calibri", "Consolas", "Segoe UI",
    ];
    const baseFonts = ["monospace", "sans-serif", "serif"];
    const testString = "mmmmmmmmmmlli";
    const testSize = "72px";

    const span = document.createElement("span");
    span.style.position = "absolute";
    span.style.left = "-9999px";
    span.style.fontSize = testSize;
    span.style.fontFamily = "monospace";
    span.innerText = testString;
    document.body.appendChild(span);

    const defaultWidth = {};
    const defaultHeight = {};
    baseFonts.forEach(b => {
        span.style.fontFamily = b;
        defaultWidth[b] = span.offsetWidth;
        defaultHeight[b] = span.offsetHeight;
    });

    let count = 0;
    fonts.forEach(font => {
        for (const base of baseFonts) {
            span.style.fontFamily = `'${font}', ${base}`;
            if (span.offsetWidth !== defaultWidth[base] || span.offsetHeight !== defaultHeight[base]) {
                count++;
                break;
            }
        }
    });
    document.body.removeChild(span);
    return count;
}

document.getElementById("btn-refresh").onclick = loadAll;
window.addEventListener("DOMContentLoaded", loadAll);