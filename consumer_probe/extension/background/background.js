const ext = globalThis.browser ?? globalThis.chrome;

chrome.runtime.onInstalled.addListener(() => {
  console.log(
    "Distributed LLM Observatory Consumer Probe installed."
  );
});

async function logLastProbe() {
  try {
    const result = await ext.storage.local.get(
      "dllo_last_probe"
    );

    console.log(
      "DLLO LAST PROBE:",
      result.dllo_last_probe ?? null
    );
  } catch (error) {
    console.error(
      "DLLO storage inspection failed:",
      error
    );
  }
}

ext.storage.onChanged.addListener(
  (changes, areaName) => {
    if (
      areaName === "local" &&
      changes.dllo_last_probe
    ) {
      console.log(
        "DLLO NEW PROBE SAVED:",
        changes.dllo_last_probe.newValue
      );
    }
  }
);

void logLastProbe();


const BRIDGE_BASE_URL =
  "http://127.0.0.1:8765";

async function hasBridgePermission() {
  return ext.permissions.contains({
    origins: [
      "http://127.0.0.1/*"
    ]
  });
}

async function bridgeJson(
  route,
  {
    method = "GET",
    body = null
  } = {}
) {
  const options = {
    method,
    cache: "no-store"
  };

  if (body !== null) {
    options.headers = {
      "Content-Type": "application/json"
    };

    options.body =
      JSON.stringify(body);
  }

  const response = await fetch(
    `${BRIDGE_BASE_URL}${route}`,
    options
  );

  let payload = null;

  try {
    payload = await response.json();
  } catch {
    payload = null;
  }

  if (!response.ok) {
    const error = new Error(
      payload?.message ??
      `Bridge returned ${response.status}.`
    );

    error.name =
      payload?.error ?? "BridgeError";

    throw error;
  }

  return payload;
}

ext.runtime.onMessage.addListener(
  async (message) => {
    const supportedTypes = new Set([
      "dllo-bridge-next",
      "dllo-telemetry-start",
      "dllo-telemetry-stop",
      "dllo-telemetry-cancel"
    ]);

    if (!supportedTypes.has(message?.type)) {
      return undefined;
    }

    try {
      if (!(await hasBridgePermission())) {
        return {
          ok: false,
          error: {
            name: "HostPermissionMissing",
            message:
              "Firefox has not granted access to 127.0.0.1."
          }
        };
      }

      if (message.type === "dllo-bridge-next") {
        await bridgeJson("/health");

        const payload =
          await bridgeJson("/v1/next");

        return {
          ok: true,
          payload
        };
      }

      if (
        typeof message.probe_id !== "string" ||
        !message.probe_id
      ) {
        throw new Error(
          "probe_id is required."
        );
      }

      const routes = {
        "dllo-telemetry-start":
          "/v1/telemetry/start",
        "dllo-telemetry-stop":
          "/v1/telemetry/stop",
        "dllo-telemetry-cancel":
          "/v1/telemetry/cancel"
      };

      const payload = await bridgeJson(
        routes[message.type],
        {
          method: "POST",
          body: {
            probe_id: message.probe_id
          }
        }
      );

      return {
        ok: true,
        payload
      };
    } catch (error) {
      console.error(
        "DLLO bridge background request failed",
        error
      );

      return {
        ok: false,
        error: {
          name:
            error?.name ?? "Error",
          message:
            error?.message ?? String(error)
        }
      };
    }
  }
);
