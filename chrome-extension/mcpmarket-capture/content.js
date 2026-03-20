const storageKey = `mcpmarket-capture:${location.pathname}${location.search}`;

function text(value) {
  return (value || "").replace(/\s+/g, " ").trim();
}

function absoluteUrl(url) {
  try {
    return new URL(url, location.origin).toString();
  } catch (_) {
    return null;
  }
}

function slugFromUrl(url) {
  try {
    const match = new URL(url).pathname.match(/^\/server\/([^/?#]+)/);
    return match ? match[1] : null;
  } catch (_) {
    return null;
  }
}

function normalizeEntry(partial, captureMethod, raw) {
  const sourceUrl = absoluteUrl(partial.source_url || location.href) || location.href;
  return {
    source: "mcpmarket",
    source_url: sourceUrl,
    slug: partial.slug || slugFromUrl(sourceUrl),
    title: partial.title || null,
    description: partial.description || null,
    categories: Array.from(new Set(partial.categories || [])).sort(),
    tags: Array.from(new Set(partial.tags || [])).sort(),
    website_url: partial.website_url || null,
    github_url: partial.github_url || null,
    pricing: partial.pricing || null,
    verified: typeof partial.verified === "boolean" ? partial.verified : null,
    capture_method: captureMethod,
    captured_at: new Date().toISOString(),
    raw: raw || {}
  };
}

function walkJson(node, found = []) {
  if (Array.isArray(node)) {
    for (const item of node) walkJson(item, found);
    return found;
  }
  if (node && typeof node === "object") {
    const hasIdentity =
      typeof node.name === "string" ||
      typeof node.title === "string" ||
      typeof node.slug === "string" ||
      typeof node.url === "string";
    if (hasIdentity) {
      found.push(node);
    }
    for (const value of Object.values(node)) walkJson(value, found);
  }
  return found;
}

function normalizeFromJsonPayload(payload, url) {
  const records = [];
  for (const node of walkJson(payload)) {
    const sourceUrl = absoluteUrl(node.url || node.source_url || url || location.href);
    const slug = node.slug || slugFromUrl(sourceUrl || "");
    if (!slug && !sourceUrl) continue;
    const githubUrl = [node.github_url, node.githubUrl, node.repository, node.repo]
      .find((candidate) => typeof candidate === "string" && candidate.includes("github.com")) || null;
    const websiteUrl = [node.website_url, node.websiteUrl, node.website, node.homepage]
      .find((candidate) => typeof candidate === "string" && candidate.startsWith("http")) || null;
    records.push(normalizeEntry({
      source_url: sourceUrl,
      slug,
      title: text(node.title || node.name),
      description: text(node.description || node.summary),
      categories: Array.isArray(node.categories) ? node.categories.map(text).filter(Boolean) : [],
      tags: Array.isArray(node.tags) ? node.tags.map(text).filter(Boolean) : [],
      website_url: websiteUrl,
      github_url: githubUrl,
      pricing: text(node.pricing || node.plan),
      verified: node.verified
    }, "network", { network_url: url, node }));
  }
  return records;
}

function normalizeFromDom() {
  const title = text(document.querySelector("h1")?.textContent) || text(document.title);
  const description = text(
    document.querySelector('meta[name="description"]')?.content ||
    document.querySelector('meta[property="og:description"]')?.content ||
    document.querySelector("main p")?.textContent
  );
  const anchors = Array.from(document.querySelectorAll("a[href]"));
  const github = anchors.find((anchor) => anchor.href.includes("github.com"))?.href || null;
  const website = anchors.find((anchor) => {
    return anchor.href.startsWith("http") &&
      !anchor.href.includes("mcpmarket.com") &&
      !anchor.href.includes("github.com");
  })?.href || null;
  return [normalizeEntry({
    source_url: location.href,
    title,
    description,
    github_url: github,
    website_url: website
  }, "dom", { title, description })];
}

async function mergeRecords(records) {
  const current = await chrome.storage.local.get(storageKey);
  const seen = new Map((current[storageKey] || []).map((record) => [record.slug || record.source_url, record]));
  for (const record of records) {
    seen.set(record.slug || record.source_url, record);
  }
  await chrome.storage.local.set({ [storageKey]: Array.from(seen.values()) });
}

window.addEventListener("message", (event) => {
  if (event.source !== window || event.data?.source !== "mcpmarket-capture-hook") {
    return;
  }
  const payload = event.data.payload || {};
  const records = payload.json ? normalizeFromJsonPayload(payload.json, payload.url) : [];
  if (records.length) {
    mergeRecords(records);
  }
});

const script = document.createElement("script");
script.src = chrome.runtime.getURL("page-hook.js");
script.onload = () => script.remove();
(document.head || document.documentElement).appendChild(script);

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type === "capture-page") {
    mergeRecords(normalizeFromDom()).then(() => sendResponse({ ok: true }));
    return true;
  }
});
