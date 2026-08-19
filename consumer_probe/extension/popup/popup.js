const startButton = document.getElementById("start-probe");
const statusElement = document.getElementById("status");
const promptInput = document.getElementById("prompt-id");

startButton.addEventListener("click", async () => {
  const promptId = promptInput.value.trim();

  if (!promptId) {
    statusElement.textContent = "Benchmark ID is required.";
    return;
  }

  const [tab] = await chrome.tabs.query({
    active: true,
    currentWindow: true
  });

  if (!tab || !tab.id) {
    statusElement.textContent = "No active tab available.";
    return;
  }

  await chrome.storage.local.set({
    dllo_probe_context: {
      prompt_id: promptId,
      started_from_extension_ms: Date.now()
    }
  });

  try {
    await chrome.scripting.executeScript({
      target: {
        tabId: tab.id
      },
      files: [
        "content/probe_overlay.js"
      ]
    });

    statusElement.textContent = "Probe started.";
    window.close();
  } catch (error) {
    console.error(error);
    statusElement.textContent = "Unable to start probe on this page.";
  }
});
