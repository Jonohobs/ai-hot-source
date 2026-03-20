async function activeTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab;
}

function storageKeyForTab(tab) {
  const url = new URL(tab.url);
  return `mcpmarket-capture:${url.pathname}${url.search}`;
}

async function readRecords(tab) {
  return chrome.runtime.sendMessage({
    type: "get-tab-records",
    key: storageKeyForTab(tab)
  });
}

async function refreshStatus() {
  const tab = await activeTab();
  const status = document.getElementById("status");
  if (!tab?.url?.startsWith("https://mcpmarket.com/")) {
    status.textContent = "Open an mcpmarket.com page first.";
    return;
  }
  const response = await readRecords(tab);
  const count = response.records.length;
  status.textContent = count
    ? `Captured ${count} record(s) for this page.`
    : "No records captured yet. Click Capture Current Page or browse so network captures fire.";
}

document.getElementById("capture").addEventListener("click", async () => {
  const tab = await activeTab();
  await chrome.tabs.sendMessage(tab.id, { type: "capture-page" });
  await refreshStatus();
});

document.getElementById("export").addEventListener("click", async () => {
  const tab = await activeTab();
  const response = await readRecords(tab);
  if (!response.records.length) {
    document.getElementById("status").textContent = "No records to export.";
    return;
  }
  const slug = new URL(tab.url).pathname.replace(/\W+/g, "_").replace(/^_+|_+$/g, "") || "page";
  await chrome.runtime.sendMessage({
    type: "download-records",
    records: response.records,
    filename: `mcpmarket-${slug}.json`
  });
  document.getElementById("status").textContent = `Exported ${response.records.length} record(s).`;
});

document.getElementById("clear").addEventListener("click", async () => {
  const tab = await activeTab();
  await chrome.runtime.sendMessage({
    type: "clear-tab-records",
    key: storageKeyForTab(tab)
  });
  await refreshStatus();
});

refreshStatus();
