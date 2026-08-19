const ext = globalThis.browser ?? globalThis.chrome;

const startButton = document.getElementById("start-probe");
const statusElement = document.getElementById("status");
const promptInput = document.getElementById("prompt-id");

function mountProbeOverlay(promptId) {
  const extensionApi = globalThis.browser ?? globalThis.chrome;
  const OVERLAY_ID = "dllo-probe-overlay";

  document.getElementById(OVERLAY_ID)?.remove();
  document.getElementById("dllo-diagnostic-marker")?.remove();

  let startedAt = null;
  let firstOutputAt = null;
  let completed = false;

  function detectPlatform(hostname) {
    if (hostname === "chatgpt.com") {
      return "chatgpt";
    }

    if (hostname === "claude.ai") {
      return "claude";
    }

    if (hostname === "gemini.google.com") {
      return "gemini";
    }

    return "other";
  }

  const overlay = document.createElement("div");
  overlay.id = OVERLAY_ID;

  Object.assign(overlay.style, {
    position: "fixed",
    top: "20px",
    right: "20px",
    zIndex: "2147483647",
    width: "310px",
    padding: "16px",
    background: "#111827",
    color: "#ffffff",
    border: "2px solid #22c55e",
    borderRadius: "10px",
    fontFamily: "system-ui, sans-serif",
    fontSize: "14px",
    boxShadow: "0 8px 30px rgba(0,0,0,.35)"
  });

  const title = document.createElement("div");
  title.textContent = "LLM Observatory Probe";
  title.style.fontWeight = "700";
  title.style.marginBottom = "6px";

  const benchmark = document.createElement("div");
  benchmark.textContent = `Benchmark: ${promptId}`;
  benchmark.style.fontSize = "12px";
  benchmark.style.marginBottom = "8px";

  const status = document.createElement("div");
  status.textContent = "Armed — ready.";
  status.style.marginBottom = "12px";

  function makeButton(label) {
    const element = document.createElement("button");

    element.textContent = label;
    element.style.margin = "3px";
    element.style.padding = "6px 9px";
    element.style.cursor = "pointer";

    return element;
  }

  const start = makeButton("Start Timer");
  const first = makeButton("First Output");
  const complete = makeButton("Complete");
  const cancel = makeButton("Cancel");

  first.disabled = true;
  complete.disabled = true;

  start.addEventListener("click", () => {
    if (startedAt !== null || completed) {
      return;
    }

    startedAt = Date.now();

    status.textContent = "Running…";

    start.disabled = true;
    first.disabled = false;
    complete.disabled = false;
  });

  first.addEventListener("click", () => {
    if (
      startedAt === null ||
      firstOutputAt !== null ||
      completed
    ) {
      return;
    }

    firstOutputAt = Date.now();

    status.textContent =
      `First output: ${firstOutputAt - startedAt} ms`;

    first.disabled = true;
  });

  complete.addEventListener("click", async () => {
    if (startedAt === null || completed) {
      return;
    }

    completed = true;

    const completedAt = Date.now();
    const hostname = window.location.hostname;

    const result = {
      schema_version: "0.1",
      probe_id: crypto.randomUUID(),

      prompt_id: promptId,
      benchmark_version: "0.1",

      platform: detectPlatform(hostname),
      page_hostname: hostname,

      started_at_ms: startedAt,
      started_at_utc: new Date(startedAt).toISOString(),

      first_output_at_ms: firstOutputAt,
      first_output_at_utc:
        firstOutputAt === null
          ? null
          : new Date(firstOutputAt).toISOString(),

      completed_at_ms: completedAt,
      completed_at_utc:
        new Date(completedAt).toISOString(),

      time_to_first_output_ms:
        firstOutputAt === null
          ? null
          : firstOutputAt - startedAt,

      total_latency_ms:
        completedAt - startedAt,

      generation_failed: false,
      interrupted: false,
      retry_observed: false,

      response_capture_enabled: false,
      response_text: null,

      measurement_mode:
        "consumer-ui-manual-v0.1"
    };

    try {
      await extensionApi.storage.local.set({
        dllo_last_probe: result
      });

      status.textContent =
        `Saved — Total: ${result.total_latency_ms} ms`;

      console.log(
        "DLLO observation saved",
        result
      );

      first.disabled = true;
      complete.disabled = true;
      start.disabled = true;

      setTimeout(() => {
        overlay.remove();
      }, 2000);
    } catch (error) {
      completed = false;

      status.textContent =
        `Storage error: ${error?.message ?? String(error)}`;

      console.error(
        "DLLO storage error",
        error
      );
    }
  });

  cancel.addEventListener("click", () => {
    completed = true;
    overlay.remove();
  });

  overlay.append(
    title,
    benchmark,
    status,
    start,
    first,
    complete,
    cancel
  );

  document.body.appendChild(overlay);
}

startButton.addEventListener("click", async () => {
  const promptId = promptInput.value.trim();

  if (!promptId) {
    statusElement.textContent =
      "Benchmark ID is required.";
    return;
  }

  try {
    const tabs = await ext.tabs.query({
      active: true,
      currentWindow: true
    });

    const tab = tabs[0];

    if (!tab?.id) {
      throw new Error("No active tab.");
    }

    await ext.scripting.executeScript({
      target: {
        tabId: tab.id
      },
      func: mountProbeOverlay,
      args: [
        promptId
      ]
    });

    statusElement.textContent = "Probe armed.";

    setTimeout(() => {
      window.close();
    }, 300);
  } catch (error) {
    console.error(error);

    statusElement.textContent =
      `ERROR: ${error?.message ?? String(error)}`;
  }
});
