chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message?.type === "download-records") {
    const blob = new Blob([JSON.stringify(message.records, null, 2)], {
      type: "application/json"
    });
    const url = URL.createObjectURL(blob);
    chrome.downloads.download({
      url,
      filename: message.filename || "mcpmarket-capture.json",
      saveAs: true
    }, () => {
      URL.revokeObjectURL(url);
      sendResponse({ ok: true });
    });
    return true;
  }

  if (message?.type === "get-tab-records") {
    chrome.storage.local.get(message.key, (result) => {
      sendResponse({ records: result[message.key] || [] });
    });
    return true;
  }

  if (message?.type === "clear-tab-records") {
    chrome.storage.local.remove(message.key, () => sendResponse({ ok: true }));
    return true;
  }
});
