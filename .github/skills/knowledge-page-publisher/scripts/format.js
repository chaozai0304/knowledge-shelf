const fs = require('fs');
const path = require('path');
const matter = require('gray-matter');
const { marked } = require('marked');

// Brand palette
// Brand palette - Inspire (Enterprise Tech)
const PRIMARY = '#10213E'; // Starry Blues
const ACCENT = '#5DB2E2';  // Creative Blue
const SECONDARY = '#625D9C'; // Amethyst
const MUTED = '#64748B';    // Text Secondary
const BG_ALT = '#F5F5F6';   // Tech Gray
const FONT = "MiSans, 'PingFang SC', system-ui, -apple-system, sans-serif";

const H2_THEMES = [
        { primary: '#6E5BFF', secondary: '#45C7FF', glow: 'rgba(110,91,255,0.24)', soft: '#F3F0FF' },
        { primary: '#0EA5E9', secondary: '#22C55E', glow: 'rgba(14,165,233,0.22)', soft: '#ECFEFF' },
        { primary: '#7C3AED', secondary: '#F472B6', glow: 'rgba(124,58,237,0.22)', soft: '#F8F0FF' },
        { primary: '#2563EB', secondary: '#14B8A6', glow: 'rgba(37,99,235,0.22)', soft: '#EFF6FF' },
        { primary: '#9333EA', secondary: '#F59E0B', glow: 'rgba(147,51,234,0.22)', soft: '#FAF5FF' }
];

const H3_THEMES = [
        { primary: '#5B7CFF', secondary: '#69EACB', soft: '#EFF3FF' },
        { primary: '#A855F7', secondary: '#F472B6', soft: '#FAF2FF' },
        { primary: '#0891B2', secondary: '#34D399', soft: '#ECFEFF' },
        { primary: '#4F46E5', secondary: '#22D3EE', soft: '#EEF2FF' }
];

const H4_THEMES = [
        { primary: '#4F46E5', secondary: '#06B6D4' },
        { primary: '#7C3AED', secondary: '#EC4899' },
        { primary: '#0F766E', secondary: '#38BDF8' }
];

let h2Index = 0;
let h3Index = 0;
let h4Index = 0;

function getTheme(list, index) {
        return list[index % list.length];
}

function createH2Icon(theme, index) {
        const gid = `h2-grad-${index}`;
        const rid = `h2-rad-${index}`;
        return `
<svg width="26" height="26" viewBox="0 0 26 26" xmlns="http://www.w3.org/2000/svg" style="display:block;flex:none;filter:drop-shadow(0 6px 14px ${theme.glow});">
    <defs>
        <linearGradient id="${gid}" x1="3" y1="3" x2="23" y2="23" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stop-color="${theme.primary}" />
            <stop offset="100%" stop-color="${theme.secondary}" />
        </linearGradient>
        <radialGradient id="${rid}" cx="0" cy="0" r="1" gradientUnits="userSpaceOnUse" gradientTransform="translate(9 8) rotate(43) scale(16 18)">
            <stop offset="0%" stop-color="#FFFFFF" stop-opacity="0.95" />
            <stop offset="100%" stop-color="#FFFFFF" stop-opacity="0" />
        </radialGradient>
    </defs>
    <rect x="2.2" y="2.2" width="21.6" height="21.6" rx="7.2" fill="url(#${gid})"/>
    <rect x="2.2" y="2.2" width="21.6" height="21.6" rx="7.2" fill="url(#${rid})" opacity="0.8"/>
    <path d="M7.5 15.5C8.9 11.2 12 8.7 17.6 8.2" stroke="rgba(255,255,255,0.72)" stroke-width="1.7" stroke-linecap="round"/>
    <path d="M9 18.2C12.4 17 15.3 14.1 16.7 10.6" stroke="rgba(255,255,255,0.88)" stroke-width="1.7" stroke-linecap="round"/>
    <circle cx="18.1" cy="8.1" r="1.8" fill="#FFFFFF"/>
    <circle cx="8.2" cy="18" r="1.45" fill="rgba(255,255,255,0.86)"/>
    <path d="M18.8 5.3L19.35 6.55L20.7 7.05L19.35 7.55L18.8 8.8L18.25 7.55L16.9 7.05L18.25 6.55L18.8 5.3Z" fill="#FFFFFF" opacity="0.98"/>
</svg>`;
}

function createH3Icon(theme, index) {
        const gid = `h3-grad-${index}`;
        return `
<svg width="18" height="18" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg" style="display:block;flex:none;filter:drop-shadow(0 4px 10px ${theme.primary}33);">
    <defs>
        <linearGradient id="${gid}" x1="2" y1="2" x2="16" y2="16" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stop-color="${theme.primary}" />
            <stop offset="100%" stop-color="${theme.secondary}" />
        </linearGradient>
    </defs>
    <path d="M9 1.5L11.15 6.2L16.5 9L11.15 11.8L9 16.5L6.85 11.8L1.5 9L6.85 6.2L9 1.5Z" fill="url(#${gid})"/>
    <path d="M9 4.2L10.1 7L12.9 8.4L10.1 9.8L9 12.6L7.9 9.8L5.1 8.4L7.9 7L9 4.2Z" fill="rgba(255,255,255,0.92)"/>
</svg>`;
}

function createH4Icon(theme, index) {
        const gid = `h4-grad-${index}`;
        return `
<svg width="14" height="14" viewBox="0 0 14 14" xmlns="http://www.w3.org/2000/svg" style="display:block;flex:none;">
    <defs>
        <linearGradient id="${gid}" x1="2" y1="2" x2="12" y2="12" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stop-color="#FFFFFF" />
            <stop offset="100%" stop-color="rgba(255,255,255,0.78)" />
        </linearGradient>
    </defs>
    <path d="M2 7H8.4" stroke="url(#${gid})" stroke-width="1.8" stroke-linecap="round"/>
    <path d="M7.2 3.8L10.6 7L7.2 10.2" stroke="url(#${gid})" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
    <circle cx="11.3" cy="7" r="1.1" fill="#FFFFFF" opacity="0.92"/>
</svg>`;
}

// Helper for Base64 encoding
function getBase64Image(imgSource, baseDir) {
    try {
        let imgPath = path.resolve(baseDir, imgSource);
        if (fs.existsSync(imgPath)) {
            const ext = path.extname(imgPath).toLowerCase().replace('.', '');
            const mimeMap = {
                jpg: 'jpeg',
                jpeg: 'jpeg',
                png: 'png',
                gif: 'gif',
                webp: 'webp',
                svg: 'svg+xml',
            };
            const mime = mimeMap[ext] || ext;
            const data = fs.readFileSync(imgPath).toString('base64');
            return `data:image/${mime};base64,${data}`;
        }
    } catch (e) {
        console.warn('Could not base64 encode image: ' + imgSource);
    }
    return imgSource;
}

// CLI Args
const args = process.argv.slice(2);
if (args.length < 2) {
    console.error('Usage: node format.js <input-md> <output-html>');
    process.exit(1);
}

const inputFile = args[0];
const outputFile = args[1];
const inputDir = path.dirname(inputFile);

if (!fs.existsSync(inputFile)) {
    console.error('Input file not found: ' + inputFile);
    process.exit(1);
}

const fileContent = fs.readFileSync(inputFile, 'utf-8');
const parsed = matter(fileContent);

// custom renderer for base64 injection
const renderer = new marked.Renderer();

renderer.heading = function (text, level) {
    if (level === 2) {
        const theme = getTheme(H2_THEMES, h2Index);
        const icon = createH2Icon(theme, h2Index);
        h2Index += 1;
        return `\n<h2 style="font-size:22px;font-weight:800;line-height:1.7em;font-family:${FONT};color:${PRIMARY};margin-top:34px;margin-bottom:18px;padding:0 0 10px 0;border-bottom:1px solid ${BG_ALT};display:flex;align-items:center;gap:10px;">` +
            `${icon}<span style="display:inline-flex;align-items:center;gap:12px;background:linear-gradient(90deg, ${theme.soft} 0%, rgba(255,255,255,0) 100%);padding:6px 14px 6px 8px;border-radius:14px;"><span style="width:6px;height:28px;border-radius:999px;background:linear-gradient(180deg, ${theme.primary} 0%, ${theme.secondary} 100%);box-shadow:0 0 0 1px ${theme.glow}, 0 6px 14px ${theme.glow};display:inline-block;"></span><span style="display:inline-block;letter-spacing:0.2px;">${text}</span></span></h2>\n`;
    }
    if (level === 3) {
        const theme = getTheme(H3_THEMES, h3Index);
        const marker = createH3Icon(theme, h3Index);
        h3Index += 1;
        return `\n<h3 style="font-size:20px;font-weight:800;line-height:1.7em;font-family:${FONT};color:${PRIMARY};margin-top:30px;margin-bottom:14px;display:flex;align-items:center;gap:8px;">` +
            `${marker}<span style="display:inline-flex;flex-direction:column;"><span style="display:inline-block;">${text}</span><span style="display:block;width:100%;height:3px;border-radius:999px;margin-top:6px;background:linear-gradient(90deg, ${theme.primary} 0%, ${theme.secondary} 100%);box-shadow:0 3px 10px ${theme.primary}22;"></span></span></h3>\n`;
    }
    if (level === 4) {
        const theme = getTheme(H4_THEMES, h4Index);
        const arrow = createH4Icon(theme, h4Index);
        h4Index += 1;
        return `\n<p style="margin-top:24px;margin-bottom:12px;"><span style="font-size:15px;font-weight:800;color:#ffffff;background:linear-gradient(135deg, ${theme.primary} 0%, ${theme.secondary} 100%);padding:6px 14px;border-radius:999px;display:inline-flex;align-items:center;gap:7px;box-shadow:0 8px 18px ${theme.primary}26, inset 0 1px 0 rgba(255,255,255,0.18);">${arrow}${text}</span></p>\n`;
    }
    return `\n<h${level}>${text}</h${level}>\n`;
};

renderer.image = function (href, title, text) {
    const b64 = getBase64Image(href, inputDir);
    return `<img src="${b64}" alt="${text || ''}" style="max-width:100%;height:auto;border-radius:8px;display:block;margin:12px 0;box-shadow:0 4px 8px rgba(0,0,0,0.1);">`;
};

function clean(s) { return s.replace(/\n/g, ' '); }

renderer.paragraph = function (text) {
    if (!text) return '\n<p></p>\n';
    if (text.trim().startsWith('<img') || text.trim().startsWith('<figure')) {
        return '\n' + text + '\n';
    }
    return `\n<p style="font-weight:400;font-family:${FONT};word-break:break-all;color:${PRIMARY};font-size:15px;line-height:1.8;margin:18px 0;">${clean(text)}</p>\n`;
};

renderer.blockquote = function (text) {
    return `\n<section style="font-family:${FONT};margin:20px 0;padding:16px;background-color:${BG_ALT};border-left:4px solid ${SECONDARY};border-radius:8px;color:${MUTED};">\n${text}\n</section>\n`;
};

renderer.list = function (body, ordered) {
    const type = ordered ? 'ol' : 'ul';
    return '\n<' + type + ' style="font-family:' + FONT + ';line-height:30px;padding-left:0;list-style:none;">\n' + body + '\n</' + type + '>\n';
};

renderer.listitem = function (text) {
    return `<li style="list-style:none;margin:8px 0;display:flex;align-items:flex-start;">` +
        `<span style="font-family:${FONT};font-size:15px;color:${ACCENT};margin-right:8px;font-weight:bold;">•</span>` +
        `<span style="font-family:${FONT};font-size:15px;color:${PRIMARY}; flex: 1;">${clean(text)}</span>` +
        `</li>\n`;
};

renderer.strong = function (text) {
    return `<span style="font-weight:bold;color:${SECONDARY};">${text}</span>`;
};

renderer.codespan = function (code) {
    return `<code style="background-color:${BG_ALT};padding:2px 6px;border-radius:4px;font-family:Consolas,Monaco,monospace;font-size:13px;color:${PRIMARY};border:1px solid ${ACCENT}33;">${code}</code>`;
};

renderer.code = function (code, lang) {
    const escaped = code.replace(/</g, '&lt;').replace(/>/g, '&gt;');
    return '\n<section style="margin:12px 0;background-color:#282c34;border-radius:5px;">' +
        '<pre style="margin:0;"><code style="overflow-x:auto;padding:12px 16px;color:#abb2bf;background:#282c34;border-radius:5px;display:block;font-family:Consolas,Monaco,Menlo,monospace;font-size:10px;line-height:1.5;white-space:pre-wrap;word-wrap:break-word;">' +
        escaped + '</code></pre></section>\n';
};

marked.setOptions({ renderer });

const title = parsed.data.title || '微信公众号排版';
const rawHtmlContent = marked.parse(parsed.content);
const escapedTitle = title.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const duplicatedTitlePattern = new RegExp(`^\\s*<h1>${escapedTitle}<\\/h1>\\s*`, 'i');
const htmlContent = rawHtmlContent.replace(duplicatedTitlePattern, '');
const author = parsed.data.author || 'chao';
const coverB64 = parsed.data.cover ? getBase64Image(parsed.data.cover, inputDir) : '';
const tags = parsed.data.tags || [];

let date = '';
if (parsed.data.date) {
    const d = new Date(parsed.data.date);
    date = !isNaN(d) ? d.toISOString().split('T')[0] : String(parsed.data.date);
}

const coverHtml = coverB64 ? `<img src="${coverB64}" alt="${title}" style="max-width:100%;height:auto;border-radius:12px;display:block;margin:0 0 24px 0;box-shadow:0 10px 30px rgba(16, 33, 62, 0.1);">` : '';
const tagsHtml = tags.length > 0 ? `\n<section style="font-family:${FONT};margin:32px 0 12px 0;padding:0;">\n${tags.map(t => `<span style="display:inline-block;font-size:12px;color:${PRIMARY};background-color:${BG_ALT};padding:4px 14px;border-radius:20px;margin:4px 8px 4px 0;border:1px solid ${ACCENT}44;font-weight:bold;"># ${t}</span>`).join('\n')}\n</section>\n` : '';

const html = `<!DOCTYPE html>
<html lang="zh_CN">
<head>
  <meta charset="utf-8">
  <title>${title}</title>
  <style>
    * { box-sizing: border-box; }
    body { background: #ffffff; color: ${PRIMARY}; margin: 0; padding: 20px; font-family: ${FONT}; }
    #page-content { max-width: 667px; margin: 0 auto; }
    .rich_media_title { font-size: 24px; font-weight: bold; line-height: 1.4; color: ${PRIMARY}; margin-bottom: 16px; }
    .rich_media_meta_list { color: ${MUTED}; font-size: 14px; margin-bottom: 32px; }
    .rich_media_meta_text { margin-right: 16px; }
    table { width: 100%; border-collapse: collapse; margin: 24px 0; font-size: 13px; }
    th, td { padding: 12px 10px; border: 1px solid ${BG_ALT}; text-align: left; vertical-align: top; }
    thead th { background-color: ${PRIMARY}; color: #ffffff; font-weight: bold; }
    tbody tr:nth-child(even) { background-color: ${BG_ALT}; }
  </style>
</head>
<body>
<div id="page-content">
  ${coverHtml}
  <h1 class="rich_media_title">${title}</h1>
  <div class="rich_media_meta_list">
    <span class="rich_media_meta_text">${author}</span>
    <span class="rich_media_meta_text">${date}</span>
  </div>
  <div id="js_content">
    ${htmlContent}
    ${tagsHtml}
  </div>
</div>
</body>
</html>`;

fs.writeFileSync(outputFile, html, 'utf-8');
console.log('Successfully generated ' + outputFile + ' with Base64 images.');
