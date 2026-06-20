const form = document.getElementById("predictForm");
const statusBox = document.getElementById("statusBox");
const submitBtn = document.getElementById("submitBtn");
const probabilitiesBox = document.getElementById("probabilities");
const imageInput = document.getElementById("image");
const imagePreview = document.getElementById("imagePreview");
const imagePlaceholder = document.getElementById("imagePlaceholder");
const lastRun = document.getElementById("lastRun");
const mq135Input = document.getElementById("mq135");
const mq2Input = document.getElementById("mq2");
const mq3Input = document.getElementById("mq3");
const mq135Stat = document.getElementById("mq135Stat");
const mq2Stat = document.getElementById("mq2Stat");
const mq3Stat = document.getElementById("mq3Stat");
const sensorCategory = document.getElementById("sensorCategory");
const sensorRealtimeScore = document.getElementById("sensorRealtimeScore");

let sensorTimer = null;

function setStatus(text, type = "info") {
  statusBox.classList.remove("hidden", "border-red-300", "bg-red-50", "text-red-700", "border-moss/35", "bg-moss/10", "text-moss");

  if (type === "error") {
    statusBox.classList.add("border-red-300", "bg-red-50", "text-red-700");
  } else {
    statusBox.classList.add("border-moss/35", "bg-moss/10", "text-moss");
  }

  statusBox.textContent = text;
}

function renderProbabilities(probabilities) {
  probabilitiesBox.innerHTML = "";

  Object.entries(probabilities).forEach(([label, value]) => {
    const row = document.createElement("div");
    row.className = "rounded-2xl border border-espresso/10 bg-sand/50 p-4";
    row.innerHTML = `
      <div class="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between sm:gap-3">
        <p class="break-words text-sm font-bold">${label}</p>
        <p class="text-xs font-semibold text-espresso/70">${value}%</p>
      </div>
      <div class="mt-2 h-2.5 rounded-full bg-espresso/10">
        <div class="h-2.5 rounded-full bg-caramel" style="width: ${Math.min(value, 100)}%"></div>
      </div>
    `;
    probabilitiesBox.appendChild(row);
  });
}

function renderSensorAnalysis(analysis) {
  const details = analysis.details || {};
  const formatText = (item) => {
    if (!item) {
      return "-";
    }
    const direction = item.delta >= 0 ? "+" : "";
    return `Nilai: ${item.value} (${direction}${item.delta}) | dev ${item.deviation_pct}%`;
  };

  mq135Stat.textContent = formatText(details.mq135);
  mq2Stat.textContent = formatText(details.mq2);
  mq3Stat.textContent = formatText(details.mq3);
  sensorCategory.textContent = analysis.category || "-";
  sensorRealtimeScore.textContent = `Skor aroma realtime: ${analysis.aroma_score ?? "-"}`;
}

function updateResult(data) {
  if (data.model_ready === false) {
    throw new Error("Model belum siap. Hasil ini bukan prediksi asli, jadi tidak ditampilkan.");
  }

  document.getElementById("gradeLabel").textContent = data.grade_label;
  document.getElementById("modelConfidence").textContent = `${data.model_confidence}%`;
  document.getElementById("aromaScore").textContent = `${data.aroma_score}`;

  if (data.sensor_analysis) {
    renderSensorAnalysis(data.sensor_analysis);
  }

  renderProbabilities(data.probabilities || {});
  lastRun.textContent = `Inferensi terakhir: ${new Date().toLocaleString("id-ID")}`;
}

async function calculateSensorRealtime() {
  const mq135 = Number(mq135Input.value || 0);
  const mq2 = Number(mq2Input.value || 0);
  const mq3 = Number(mq3Input.value || 0);

  if (mq135 < 0 || mq2 < 0 || mq3 < 0) {
    mq135Stat.textContent = "Nilai tidak boleh negatif";
    mq2Stat.textContent = "Nilai tidak boleh negatif";
    mq3Stat.textContent = "Nilai tidak boleh negatif";
    sensorCategory.textContent = "Input tidak valid";
    sensorRealtimeScore.textContent = "Skor aroma realtime: -";
    return;
  }

  try {
    const response = await fetch("/sensor/calculate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ mq135, mq2, mq3 }),
    });

    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "Gagal menghitung sensor.");
    }

    renderSensorAnalysis(payload);
  } catch (err) {
    sensorCategory.textContent = "Error";
    sensorRealtimeScore.textContent = `Skor aroma realtime: ${err.message}`;
  }
}

function queueSensorCalculation() {
  if (sensorTimer) {
    clearTimeout(sensorTimer);
  }
  sensorTimer = setTimeout(calculateSensorRealtime, 250);
}

function handleImagePreview(event) {
  const file = event.target.files && event.target.files[0];
  if (!file) {
    return;
  }

  const maxFileSize = 50 * 1024 * 1024;
  if (file.size > maxFileSize) {
    setStatus(`File terlalu besar (${(file.size / 1024 / 1024).toFixed(1)}MB). Maksimal 50MB.`, "error");
    event.target.value = "";
    imagePreview.classList.add("hidden");
    imagePreview.removeAttribute("src");
    imagePlaceholder.classList.remove("hidden");
    return;
  }

  const fileUrl = URL.createObjectURL(file);
  imagePreview.src = fileUrl;
  imagePreview.classList.remove("hidden");
  imagePlaceholder.classList.add("hidden");
  statusBox.classList.add("hidden");
}

async function handleSubmit(event) {
  event.preventDefault();
  const formData = new FormData(form);

  submitBtn.disabled = true;
  submitBtn.classList.add("opacity-60", "cursor-not-allowed");
  setStatus("Sedang menjalankan inferensi model...");

  try {
    const response = await fetch("/predict", {
      method: "POST",
      body: formData,
    });

    let payload;
    try {
      payload = await response.json();
    } catch {
      throw new Error(`Server error: ${response.status} ${response.statusText}`);
    }

    if (!response.ok) {
      throw new Error(payload.error || `Inferensi gagal (${response.status}).`);
    }

    updateResult(payload);
    setStatus("Inferensi selesai. Hasil sudah diperbarui.");
  } catch (err) {
    setStatus(err.message, "error");
  } finally {
    submitBtn.disabled = false;
    submitBtn.classList.remove("opacity-60", "cursor-not-allowed");
  }
}

[mq135Input, mq2Input, mq3Input].forEach((input) => {
  input.addEventListener("input", queueSensorCalculation);
});

imageInput.addEventListener("change", handleImagePreview);
form.addEventListener("submit", handleSubmit);

calculateSensorRealtime();
