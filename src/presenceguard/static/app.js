const camera = document.querySelector("#camera");
const canvas = document.querySelector("#capture-canvas");
const cameraState = document.querySelector("#camera-state");
const result = document.querySelector("#result");
let stream = null;

function showResult(kicker, message, isError = false) {
  result.classList.toggle("error", isError);
  result.innerHTML = `<span class="result-kicker">${kicker}</span><strong>${message}</strong>`;
}

function safeMessage(payload, fallback) {
  return payload?.error?.message || fallback;
}

async function startCamera() {
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: "user", width: { ideal: 960 }, height: { ideal: 720 } },
      audio: false,
    });
    camera.srcObject = stream;
    await camera.play();
    cameraState.textContent = "Camera ready · one face only";
    showResult("Ready", "Centre one face inside the guide.");
  } catch (error) {
    showResult("Camera blocked", "Allow camera access in your browser settings.", true);
  }
}

async function captureFrame() {
  if (!stream || camera.readyState < 2) {
    throw new Error("Start the camera first.");
  }
  const width = camera.videoWidth;
  const height = camera.videoHeight;
  canvas.width = width;
  canvas.height = height;
  const context = canvas.getContext("2d", { alpha: false });
  context.translate(width, 0);
  context.scale(-1, 1);
  context.drawImage(camera, 0, 0, width, height);
  return new Promise((resolve, reject) => {
    canvas.toBlob(
      (blob) => (blob ? resolve(blob) : reject(new Error("Could not capture a frame."))),
      "image/jpeg",
      0.88,
    );
  });
}

document.querySelector("#start-camera").addEventListener("click", startCamera);

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((candidate) => {
      const active = candidate === tab;
      candidate.classList.toggle("active", active);
      candidate.setAttribute("aria-selected", String(active));
    });
    document.querySelector("#checkin-panel").classList.toggle("hidden", tab.dataset.panel !== "checkin");
    document.querySelector("#enroll-panel").classList.toggle("hidden", tab.dataset.panel !== "enroll");
  });
});

document.querySelector("#verify").addEventListener("click", async (event) => {
  const button = event.currentTarget;
  const participantId = document.querySelector("#checkin-id").value.trim();
  if (!participantId) {
    showResult("Missing ID", "Enter a participant ID.", true);
    return;
  }
  button.disabled = true;
  try {
    showResult("Processing", "Checking face quality and encrypted references…");
    const frame = await captureFrame();
    const form = new FormData();
    form.append("image", frame, "verification.jpg");
    const response = await fetch(`/api/v1/participants/${encodeURIComponent(participantId)}/verification`, {
      method: "POST",
      headers: { "Idempotency-Key": crypto.randomUUID() },
      body: form,
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(safeMessage(payload, "Verification failed."));
    if (payload.status === "verified") {
      showResult("Attendance recorded", `Verified with score ${payload.score.toFixed(3)}.`);
    } else if (payload.status === "duplicate") {
      showResult("Already checked in", "A recent attendance record already exists.");
    } else {
      showResult("Not verified", `Score ${payload.score.toFixed(3)} did not meet the threshold.`, true);
    }
  } catch (error) {
    showResult("Verification stopped", error.message, true);
  } finally {
    button.disabled = false;
  }
});

document.querySelector("#enroll").addEventListener("click", async (event) => {
  const button = event.currentTarget;
  const participantId = document.querySelector("#enroll-id").value.trim();
  const displayName = document.querySelector("#display-name").value.trim();
  const adminToken = document.querySelector("#admin-token").value;
  const consent = document.querySelector("#consent").checked;
  if (!participantId || !displayName || !adminToken || !consent) {
    showResult("Enrollment incomplete", "Enter all fields and confirm consent.", true);
    return;
  }
  button.disabled = true;
  try {
    const form = new FormData();
    form.append("display_name", displayName);
    form.append("consent_confirmed", "true");
    for (let index = 0; index < 50; index += 1) {
      showResult("Capturing", `Hold still, then turn slightly · ${index + 1} / 50`);
      const frame = await captureFrame();
      form.append("images", frame, `enrollment-${index + 1}.jpg`);
      await new Promise((resolve) => setTimeout(resolve, 110));
    }
    showResult("Encrypting", "Creating the local biometric template…");
    const response = await fetch(`/api/v1/participants/${encodeURIComponent(participantId)}/enrollment`, {
      method: "POST",
      headers: { "X-Admin-Token": adminToken },
      body: form,
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(safeMessage(payload, "Enrollment failed."));
    showResult(
      "Enrollment complete",
      `${payload.accepted_samples} references encrypted; ${payload.rejected_samples} discarded.`,
    );
  } catch (error) {
    showResult("Enrollment stopped", error.message, true);
  } finally {
    button.disabled = false;
  }
});

window.addEventListener("beforeunload", () => {
  stream?.getTracks().forEach((track) => track.stop());
});
