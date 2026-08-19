(() => {
  const old = document.getElementById("dllo-probe-overlay");

  if (old) {
    old.remove();
  }

  const overlay = document.createElement("div");
  overlay.id = "dllo-probe-overlay";

  overlay.style.position = "fixed";
  overlay.style.top = "20px";
  overlay.style.right = "20px";
  overlay.style.zIndex = "2147483647";
  overlay.style.width = "300px";
  overlay.style.padding = "16px";
  overlay.style.background = "#111827";
  overlay.style.color = "#ffffff";
  overlay.style.border = "2px solid #22c55e";
  overlay.style.borderRadius = "10px";
  overlay.style.fontFamily = "sans-serif";

  const title = document.createElement("strong");
  title.textContent = "LLM Observatory Probe";

  const status = document.createElement("p");
  status.textContent = "Injection successful — probe ready.";

  const button = document.createElement("button");
  button.textContent = "TEST BUTTON";

  button.addEventListener("click", () => {
    status.textContent = "Button works!";
  });

  overlay.appendChild(title);
  overlay.appendChild(status);
  overlay.appendChild(button);

  document.body.appendChild(overlay);

  console.log("DLLO minimal overlay mounted");
})();
