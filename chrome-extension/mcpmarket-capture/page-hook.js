(function () {
  if (window.__MCPMARKET_CAPTURE_INSTALLED__) {
    return;
  }
  window.__MCPMARKET_CAPTURE_INSTALLED__ = true;

  const postCapture = (kind, payload) => {
    window.postMessage({
      source: "mcpmarket-capture-hook",
      kind,
      payload
    }, "*");
  };

  const originalFetch = window.fetch;
  window.fetch = async function (...args) {
    const response = await originalFetch.apply(this, args);
    try {
      const url = typeof args[0] === "string" ? args[0] : args[0]?.url;
      if (url && url.includes("mcpmarket.com")) {
        const clone = response.clone();
        const contentType = clone.headers.get("content-type") || "";
        if (contentType.includes("application/json")) {
          clone.json().then((json) => postCapture("fetch", { url, json })).catch(() => {});
        } else {
          clone.text().then((text) => postCapture("fetch-text", { url, text })).catch(() => {});
        }
      }
    } catch (_) {}
    return response;
  };

  const originalOpen = XMLHttpRequest.prototype.open;
  const originalSend = XMLHttpRequest.prototype.send;

  XMLHttpRequest.prototype.open = function (method, url, ...rest) {
    this.__mcpmarket_capture = { method, url };
    return originalOpen.call(this, method, url, ...rest);
  };

  XMLHttpRequest.prototype.send = function (...args) {
    this.addEventListener("load", function () {
      try {
        const url = this.__mcpmarket_capture?.url;
        const contentType = this.getResponseHeader("content-type") || "";
        if (url && url.includes("mcpmarket.com")) {
          if (contentType.includes("application/json")) {
            postCapture("xhr", { url, json: JSON.parse(this.responseText) });
          } else {
            postCapture("xhr-text", { url, text: this.responseText });
          }
        }
      } catch (_) {}
    });
    return originalSend.apply(this, args);
  };
})();
