const ext = globalThis.browser ?? globalThis.chrome;

const HISTORY_KEY = "dllo_probe_history";
const LAST_PROBE_KEY = "dllo_last_probe";
const MAX_LOCAL_HISTORY = 2000;

const BRIDGE_BASE_URL =
  "http://127.0.0.1:8765";

let bridgePromptId = null;
let bridgePromptText = null;
let bridgeScheduledAtUtc = null;

const ALLOWED_HOSTS = new Set([
  "chatgpt.com",
  "claude.ai",
  "gemini.google.com"
]);

const startButton = document.getElementById("start-probe");
const exportButton = document.getElementById("export-json");
const statusElement = document.getElementById("status");
const promptInput = document.getElementById("prompt-id");
const sampleCount = document.getElementById("sample-count");
const lastMeasurement = document.getElementById("last-measurement");

const benchmarkPreview =
  document.createElement("div");

benchmarkPreview.id = "benchmark-preview";
benchmarkPreview.hidden = true;

Object.assign(benchmarkPreview.style, {
  marginTop: "8px",
  marginBottom: "10px",
  padding: "10px",
  maxHeight: "150px",
  overflowY: "auto",
  whiteSpace: "pre-wrap",
  background: "#1f2937",
  borderRadius: "6px",
  fontSize: "12px",
  lineHeight: "1.4"
});

promptInput.parentElement.insertBefore(
  benchmarkPreview,
  startButton
);

const connectBridgeButton =
  document.createElement("button");

connectBridgeButton.id = "connect-bridge";
connectBridgeButton.textContent =
  "Connect DLLO Bridge";

startButton.parentElement.insertBefore(
  connectBridgeButton,
  startButton
);


function hostnameFromUrl(urlString) {
  try {
    return new URL(urlString).hostname;
  } catch {
    return null;
  }
}


function platformFromHostname(hostname) {
  if (hostname === "chatgpt.com") {
    return "chatgpt";
  }

  if (hostname === "claude.ai") {
    return "claude";
  }

  if (hostname === "gemini.google.com") {
    return "gemini";
  }

  return null;
}


function showBenchmarkPreview(
  promptText
) {
  if (!promptText) {
    benchmarkPreview.textContent = "";
    benchmarkPreview.hidden = true;
    return;
  }

  benchmarkPreview.textContent =
    promptText;

  benchmarkPreview.hidden = false;
}


async function hasBridgePermission() {
  return ext.permissions.contains({
    origins: [
      "http://127.0.0.1/*"
    ]
  });
}


async function requestBridgePermission() {
  try {
    const granted =
      await ext.permissions.request({
        origins: [
          "http://127.0.0.1/*"
        ]
      });

    if (!granted) {
      statusElement.textContent =
        "DLLO Bridge permission was not granted.";
      return;
    }

    connectBridgeButton.hidden = true;

    statusElement.textContent =
      "DLLO Bridge connected.";

    await refreshBridgeRecommendation();
  } catch (error) {
    console.error(
      "DLLO bridge permission request failed",
      error
    );

    statusElement.textContent =
      `Bridge permission error: ${
        error?.message ?? String(error)
      }`;
  }
}


async function refreshBridgeRecommendation() {
  let bridgeStage = "startup";

  try {
    const permitted =
      await hasBridgePermission();

    if (!permitted) {
      connectBridgeButton.hidden = false;

      statusElement.textContent =
        "Bridge disconnected — connect to enable scheduling.";

      showBenchmarkPreview(null);

      return;
    }

    connectBridgeButton.hidden = true;
    let loopbackPermission = "unknown";

    try {
      const permission =
        await navigator.permissions.query({
          name: "loopback-network"
        });

      loopbackPermission =
        permission.state;
    } catch (error) {
      console.debug(
        "DLLO loopback permission query failed",
        error
      );
    }

    console.log(
      "DLLO loopback permission:",
      loopbackPermission
    );

    const tabs = await ext.tabs.query({
      active: true,
      currentWindow: true
    });

    const tab = tabs[0];

    if (!tab?.url) {
      throw new Error(
        "No active browser tab."
      );
    }

    const hostname =
      hostnameFromUrl(tab.url);

    if (!ALLOWED_HOSTS.has(hostname)) {
      statusElement.textContent =
        "Bridge idle — unsupported site.";
      return;
    }

    const activePlatform =
      platformFromHostname(hostname);

    bridgeStage = "background";

    const bridgeResponse =
      await ext.runtime.sendMessage({
        type: "dllo-bridge-next"
      });

    if (!bridgeResponse?.ok) {
      const errorName =
        bridgeResponse?.error?.name
        ?? "BridgeError";

      const errorMessage =
        bridgeResponse?.error?.message
        ?? "Background bridge request failed.";

      throw new Error(
        `${errorName}: ${errorMessage}`
      );
    }

    const payload =
      bridgeResponse.payload;

    if (payload.platform !== activePlatform) {
      statusElement.textContent =
        `Bridge configured for ${
          payload.platform
        }; active site is ${activePlatform}.`;

      return;
    }

    if (
      payload.status === "due" &&
      payload.item?.prompt_id
    ) {
      promptInput.value =
        payload.item.prompt_id;

      bridgePromptId =
        payload.item.prompt_id;

      bridgePromptText =
        payload.item.prompt;

      bridgeScheduledAtUtc =
        payload.item.scheduled_at_utc;

      showBenchmarkPreview(
        payload.item.prompt
      );

      statusElement.textContent =
        `Due now · ${
          payload.item.prompt_id
        }`;

      return;
    }

    if (
      payload.status === "upcoming" &&
      payload.item?.prompt_id
    ) {
      promptInput.value =
        payload.item.prompt_id;

      bridgePromptId =
        payload.item.prompt_id;

      bridgePromptText =
        payload.item.prompt;

      bridgeScheduledAtUtc =
        payload.item.scheduled_at_utc;

      showBenchmarkPreview(
        payload.item.prompt
      );

      const minutes = Math.max(
        0,
        Math.round(
          payload.item.starts_in_ms
          / 60000
        )
      );

      statusElement.textContent =
        `Upcoming · ${
          payload.item.prompt_id
        } · ${minutes} min`;

      return;
    }

    if (payload.status === "none") {
      bridgePromptId = null;
      bridgePromptText = null;
      bridgeScheduledAtUtc = null;

      showBenchmarkPreview(null);

      statusElement.textContent =
        "No scheduled probe remaining today.";

      return;
    }

    throw new Error(
      "Unexpected bridge response."
    );
  } catch (error) {
    console.debug(
      "DLLO localhost bridge unavailable",
      error
    );

    statusElement.textContent =
      `Bridge error [${bridgeStage}]: ${
        error?.name ?? "Error"
      } · ${
        error?.message ?? String(error)
      }`;
  }
}


async function refreshLocalSummary() {
  const data = await ext.storage.local.get([
    HISTORY_KEY,
    LAST_PROBE_KEY
  ]);

  const history = data[HISTORY_KEY] ?? [];
  const lastProbe = data[LAST_PROBE_KEY] ?? null;

  sampleCount.textContent = String(history.length);

  if (!lastProbe) {
    lastMeasurement.textContent =
      "No measurements yet.";
    return;
  }

  const totalSeconds =
    lastProbe.total_latency_ms / 1000;

  const ttfo =
    lastProbe.time_to_first_output_ms === null
      ? "n/a"
      : `${lastProbe.time_to_first_output_ms} ms`;

  lastMeasurement.textContent =
    `Last: ${totalSeconds.toFixed(2)} s · Human-observed first output ${ttfo}`;
}


function mountProbeOverlay(
  promptId,
  promptText,
  scheduledAtUtc,
  historyKey,
  lastProbeKey,
  maxHistory
) {
  const extensionApi =
    globalThis.browser ?? globalThis.chrome;

  const OVERLAY_ID = "dllo-probe-overlay";

  document.getElementById(OVERLAY_ID)?.remove();
  document.getElementById(
    "dllo-diagnostic-marker"
  )?.remove();

  let startedAt = null;
  let firstOutputAt = null;
  let completed = false;

  let probeId = null;
  let telemetryStartPromise = null;
  let telemetryFinalized = false;
  let localTelemetry = null;
  let localTelemetryError = null;

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
  benchmark.textContent =
    `Benchmark: ${promptId}`;
  benchmark.style.fontSize = "12px";
  benchmark.style.marginBottom = "8px";

  const promptPreview =
    document.createElement("div");

  if (promptText) {
    promptPreview.textContent = promptText;

    Object.assign(promptPreview.style, {
      marginBottom: "10px",
      padding: "8px",
      maxHeight: "140px",
      overflowY: "auto",
      whiteSpace: "pre-wrap",
      background: "#1f2937",
      borderRadius: "6px",
      fontSize: "12px",
      lineHeight: "1.4"
    });
  }

  const status = document.createElement("div");
  status.textContent = "Armed — ready.";
  status.style.marginBottom = "12px";

  function makeButton(label) {
    const element =
      document.createElement("button");

    element.textContent = label;
    element.style.margin = "3px";
    element.style.padding = "6px 9px";
    element.style.cursor = "pointer";

    return element;
  }

  const start = makeButton("Start Timer");
  const first = makeButton("Mark First Output (Human)");
  const complete = makeButton("Complete");
  const cancel = makeButton("Cancel");

  first.disabled = true;
  complete.disabled = true;

  start.addEventListener("click", () => {
    if (startedAt !== null || completed) {
      return;
    }

    probeId = crypto.randomUUID();
    startedAt = Date.now();

    telemetryStartPromise =
      extensionApi.runtime.sendMessage({
        type: "dllo-telemetry-start",
        probe_id: probeId
      });

    void telemetryStartPromise
      .then((response) => {
        if (
          !completed &&
          !response?.ok
        ) {
          status.textContent =
            "Running… · local telemetry unavailable";
        }
      })
      .catch((error) => {
        if (!completed) {
          status.textContent =
            "Running… · local telemetry unavailable";
        }

        console.warn(
          "DLLO telemetry start failed",
          error
        );
      });

    status.textContent = "Running…";

    start.disabled = true;
    first.disabled = false;
    complete.disabled = false;
  });

  async function stopLocalTelemetry() {
    if (telemetryFinalized) {
      return;
    }

    telemetryFinalized = true;

    if (
      probeId === null ||
      telemetryStartPromise === null
    ) {
      return;
    }

    try {
      const startResponse =
        await telemetryStartPromise;

      if (!startResponse?.ok) {
        localTelemetryError =
          startResponse?.error?.message ??
          "Local telemetry did not start.";
        return;
      }

      const stopResponse =
        await extensionApi.runtime.sendMessage({
          type: "dllo-telemetry-stop",
          probe_id: probeId
        });

      if (!stopResponse?.ok) {
        localTelemetryError =
          stopResponse?.error?.message ??
          "Local telemetry could not be stopped.";
        return;
      }

      localTelemetry =
        stopResponse.payload ?? null;
    } catch (error) {
      localTelemetryError =
        error?.message ?? String(error);

      console.warn(
        "DLLO telemetry stop failed",
        error
      );
    }
  }

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
      `First output: ${
        firstOutputAt - startedAt
      } ms`;

    first.disabled = true;
  });

  complete.addEventListener(
    "click",
    async () => {
      if (startedAt === null || completed) {
        return;
      }

      completed = true;

      const completedAt = Date.now();
      const hostname =
        window.location.hostname;

      status.textContent =
        "Stopping local telemetry…";

      await stopLocalTelemetry();

      const result = {
        schema_version: "0.1",
        probe_id: probeId,

        prompt_id: promptId,
        benchmark_version: "0.1",

        scheduled_at_utc:
          scheduledAtUtc ?? null,

        schedule_offset_ms:
          scheduledAtUtc === null
            ? null
            : startedAt
              - Date.parse(scheduledAtUtc),

        platform: detectPlatform(hostname),
        page_hostname: hostname,

        started_at_ms: startedAt,
        started_at_utc:
          new Date(startedAt).toISOString(),

        first_output_at_ms: firstOutputAt,
        first_output_at_utc:
          firstOutputAt === null
            ? null
            : new Date(
                firstOutputAt
              ).toISOString(),

        completed_at_ms: completedAt,
        completed_at_utc:
          new Date(
            completedAt
          ).toISOString(),

        time_to_first_output_ms:
          firstOutputAt === null
            ? null
            : firstOutputAt - startedAt,

        first_output_measurement_mode:
          firstOutputAt === null
            ? null
            : "human-observed-click-v0.1",

        total_latency_ms:
          completedAt - startedAt,

        generation_failed: false,
        interrupted: false,
        retry_observed: false,

        response_capture_enabled: false,
        response_text: null,

        measurement_mode:
          "consumer-ui-manual-v0.1",

        local_telemetry:
          localTelemetry,

        local_telemetry_error:
          localTelemetryError
      };

      try {
        const stored =
          await extensionApi.storage.local.get(
            historyKey
          );

        const history =
          stored[historyKey] ?? [];

        history.push(result);

        const trimmedHistory =
          history.slice(-maxHistory);

        await extensionApi.storage.local.set({
          [lastProbeKey]: result,
          [historyKey]: trimmedHistory
        });

        status.textContent =
          `Saved — sample #${
            trimmedHistory.length
          }`;

        console.log(
          "DLLO observation saved",
          result
        );

        first.disabled = true;
        complete.disabled = true;
        start.disabled = true;

        setTimeout(() => {
          overlay.remove();
        }, 1800);
      } catch (error) {
        completed = false;

        status.textContent =
          `Storage error: ${
            error?.message ?? String(error)
          }`;

        console.error(
          "DLLO storage error",
          error
        );
      }
    }
  );

  cancel.addEventListener("click", () => {
    completed = true;
    overlay.remove();

    if (
      telemetryFinalized ||
      probeId === null ||
      telemetryStartPromise === null
    ) {
      return;
    }

    telemetryFinalized = true;

    void telemetryStartPromise
      .then(async (startResponse) => {
        if (!startResponse?.ok) {
          return;
        }

        await extensionApi.runtime.sendMessage({
          type: "dllo-telemetry-cancel",
          probe_id: probeId
        });
      })
      .catch((error) => {
        console.warn(
          "DLLO telemetry cancel failed",
          error
        );
      });
  });

  overlay.append(
    title,
    benchmark
  );

  if (promptText) {
    overlay.append(promptPreview);
  }

  overlay.append(
    status,
    start,
    first,
    complete,
    cancel
  );

  document.body.appendChild(overlay);
}


connectBridgeButton.addEventListener(
  "click",
  requestBridgePermission
);


startButton.addEventListener(
  "click",
  async () => {
    const promptId =
      promptInput.value.trim();

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

      if (!tab?.id || !tab.url) {
        throw new Error(
          "No active browser tab."
        );
      }

      const hostname =
        hostnameFromUrl(tab.url);

      if (!ALLOWED_HOSTS.has(hostname)) {
        throw new Error(
          "Probe allowed only on ChatGPT, Claude or Gemini."
        );
      }

      const usesScheduledPrompt =
        promptId === bridgePromptId;

      const promptText =
        usesScheduledPrompt
          ? bridgePromptText
          : null;

      const scheduledAtUtc =
        usesScheduledPrompt
          ? bridgeScheduledAtUtc
          : null;

      await ext.scripting.executeScript({
        target: {
          tabId: tab.id
        },
        func: mountProbeOverlay,
        args: [
          promptId,
          promptText,
          scheduledAtUtc,
          HISTORY_KEY,
          LAST_PROBE_KEY,
          MAX_LOCAL_HISTORY
        ]
      });

      statusElement.textContent =
        `Probe armed on ${hostname}.`;

      setTimeout(() => {
        window.close();
      }, 300);
    } catch (error) {
      console.error(error);

      statusElement.textContent =
        `ERROR: ${
          error?.message ?? String(error)
        }`;
    }
  }
);


exportButton.addEventListener(
  "click",
  async () => {
    try {
      const data =
        await ext.storage.local.get(
          HISTORY_KEY
        );

      const records =
        data[HISTORY_KEY] ?? [];

      if (records.length === 0) {
        statusElement.textContent =
          "No samples to export.";
        return;
      }

      const payload = {
        export_schema_version: "0.1",
        exported_at_utc:
          new Date().toISOString(),
        sample_count: records.length,
        records
      };

      const blob = new Blob(
        [
          JSON.stringify(
            payload,
            null,
            2
          )
        ],
        {
          type: "application/json"
        }
      );

      const url =
        URL.createObjectURL(blob);

      const anchor =
        document.createElement("a");

      const stamp =
        new Date()
          .toISOString()
          .replaceAll(":", "-")
          .replaceAll(".", "-");

      anchor.href = url;
      anchor.download =
        `dllo-consumer-probes-${stamp}.json`;

      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();

      URL.revokeObjectURL(url);

      statusElement.textContent =
        `Exported ${records.length} samples.`;
    } catch (error) {
      console.error(error);

      statusElement.textContent =
        `Export error: ${
          error?.message ?? String(error)
        }`;
    }
  }
);


void refreshLocalSummary();


void refreshBridgeRecommendation();
