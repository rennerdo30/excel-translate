const elements = {
  healthButton: document.getElementById("healthButton"),
  status: document.getElementById("status"),
};

Office.onReady(async (info) => {
  if (info.host !== Office.HostType.Excel) {
    setStatus("Open this add-in from Excel.");
    elements.healthButton.disabled = true;
    return;
  }

  elements.healthButton.addEventListener("click", checkHealth);
  setStatus(
    "Ready.\nOpen the add-in once to register the formulas, then use XLT.TRANSLATE or XLT.TRANSLATE_RANGE in worksheet cells."
  );
});

async function checkHealth() {
  elements.healthButton.disabled = true;
  setStatus("Checking the local add-in host...");

  try {
    const response = await fetch("/api/health");
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Health check failed.");
    }

    setStatus(
      `${data.message}\nDefault provider: ${data.defaultProvider}\nLM Studio URL: ${data.lmStudioBaseUrl}\nActive model: ${data.activeModel}\nConfigured model override: ${data.configuredModel || "(auto)"}\n\nNext step: use =XLT.TRANSLATE(A1,"de") in a worksheet cell.`
    );
  } catch (error) {
    setStatus(`Health check failed.\n${error.message || error}`);
  } finally {
    elements.healthButton.disabled = false;
  }
}

function setStatus(message) {
  elements.status.textContent = message;
}
