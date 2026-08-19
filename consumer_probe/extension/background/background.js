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


ext.runtime.onMessage.addListener(
  async (message) => {
    if (message?.type !== "dllo-bridge-next") {
      return undefined;
    }

    try {
      const hasBridgePermission =
        await ext.permissions.contains({
          origins: [
            "http://127.0.0.1/*"
          ]
        });

      if (!hasBridgePermission) {
        return {
          ok: false,
          error: {
            name: "HostPermissionMissing",
            message:
              "Firefox has not granted access to 127.0.0.1."
          }
        };
      }

      const healthResponse = await fetch(
        "http://127.0.0.1:8765/health",
        {
          cache: "no-store"
        }
      );

      if (!healthResponse.ok) {
        throw new Error(
          `Bridge health returned ${
            healthResponse.status
          }.`
        );
      }

      const nextResponse = await fetch(
        "http://127.0.0.1:8765/v1/next",
        {
          cache: "no-store"
        }
      );

      if (!nextResponse.ok) {
        throw new Error(
          `Bridge next returned ${
            nextResponse.status
          }.`
        );
      }

      const payload =
        await nextResponse.json();

      return {
        ok: true,
        payload
      };
    } catch (error) {
      console.error(
        "DLLO bridge background fetch failed",
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
