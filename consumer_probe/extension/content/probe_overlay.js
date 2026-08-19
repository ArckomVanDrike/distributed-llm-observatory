(() => {
  const existing = document.getElementById("dllo-probe-overlay");

  if (existing) {
    existing.remove();
  }

  const startedAt = Date.now();
  let firstOutputAt = null;

  const overlay = document.createElement("div");
  overlay.id = "dllo-probe-overlay";

  Object.assign(overlay.style, {
    position: "fixed",
    top: "20px",
    right: "20px",
    zIndex: "2147483647",
    width: "260px",
    padding: "14px",
    background: "#111827",
    color: "#f9fafb",
    border: "1px solid #374151",
    borderRadius: "10px",
    fontFamily: "system-ui, sans-serif",
    fontSize: "14px",
    boxShadow: "0 8px 30px rgba(0,0,0,0.35)"
  });

  const title = document.createElement("div");
  title.textContent = "LLM Observatory Probe";
  title.style.fontWeight = "700";
  title.style.marginBottom = "10px";

  const status = document.createElement("div");
  status.textContent = "Probe running…";
  status.style.marginBottom = "12px";

  const firstOutputButton = document.createElement("button");
  firstOutputButton.textContent = "Mark First Output";
  firstOutputButton.style.marginRight = "6px";

  const completeButton = document.createElement("button");
  completeButton.textContent = "Complete";

  const closeButton = document.createElement("button");
  closeButton.textContent = "Cancel";
  closeButton.style.marginLeft = "6px";

  firstOutputButton.addEventListener("click", async () => {
    if (firstOutputAt !== null) {
      return;
    }

    firstOutputAt = Date.now();

    const ttfo = firstOutputAt - startedAt;

    status.textContent = `First output: ${ttfo} ms`;
    firstOutputButton.disabled = true;

    await chrome.storage.local.set({
      dllo_probe_active: {
        started_at_ms: startedAt,
        first_output_at_ms: firstOutputAt
      }
    });
  });

  completeButton.addEventListener("click", async () => {
    const completedAt = Date.now();

    const result = {
      started_at_ms: startedAt,
      first_output_at_ms: firstOutputAt,
      completed_at_ms: completedAt,
      time_to_first_output_ms:
        firstOutputAt === null ? null : firstOutputAt - startedAt,
      total_latency_ms: completedAt - startedAt,
      page_hostname: window.location.hostname
    };

    await chrome.storage.local.set({
      dllo_last_probe: result
    });

    console.log("DLLO probe result:", result);

    overlay.remove();
  });

  closeButton.addEventListener("click", () => {
    overlay.remove();
  });

  overlay.appendChild(title);
  overlay.appendChild(status);
  overlay.appendChild(firstOutputButton);
  overlay.appendChild(completeButton);
  overlay.appendChild(closeButton);

  document.documentElement.appendChild(overlay);
})();
