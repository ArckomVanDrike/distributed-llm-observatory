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
