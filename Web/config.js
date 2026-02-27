const config = {
  minDelay: 5,
  maxDelay: 15,
  alertChance: 0.10,

  plateFormat: {
    letters: 3,
    numbers: 4,
  },

  letters: [
    { ar: "أ", en: "A" },
    { ar: "ب", en: "B" },
    { ar: "ح", en: "J" },
    { ar: "د", en: "D" },
    { ar: "ر", en: "R" },
    { ar: "س", en: "S" },
    { ar: "ص", en: "X" },
    { ar: "ط", en: "T" },
    { ar: "ع", en: "E" },
    { ar: "ق", en: "G" },
    { ar: "ك", en: "K" },
    { ar: "ل", en: "L" },
    { ar: "م", en: "Z" },
    { ar: "ن", en: "N" },
    { ar: "هـ", en: "H" },
    { ar: "و", en: "U" },
    { ar: "ى", en: "V" },
  ],

  forbidden: ["SEX", "ASS", "USA", "GOD"],

  cameras: [
    { id: "C-01", location: "طريق الملك عبدالله - تبوك" },
    { id: "C-02", location: "طريق المدينة - تبوك" },
    { id: "C-03", location: "طريق الملك فهد - تبوك" },
    { id: "C-04", location: "تقاطع الأمير فهد - تبوك" },
    { id: "C-05", location: "طريق الملك خالد - تبوك" },
  ],

  serverUrl: "http://localhost:5000/api/check",
};


// ✅ الدالة الوحيدة
function sendEvent(generatedPlate) {
  const formData = new FormData();
  formData.append("plate_number", generatedPlate);

  fetch(config.serverUrl, {
    method: "POST",
    body: formData
  })
  .then(res => res.json())
  .then(data => console.log("Check result:", data))
  .catch(err => console.error("Error:", err));
}