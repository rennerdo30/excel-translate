Office.onReady(() => {
  // The custom-functions runtime loads this page to register formulas.
});

async function translate(text, targetLanguage, sourceLanguage) {
  const normalizedText = normalizeScalar(text);
  const target = normalizeLanguage(targetLanguage);
  const source = normalizeLanguage(sourceLanguage, "auto");

  if (!normalizedText) {
    return "";
  }

  if (!target) {
    return "[translation failed: target language is required]";
  }

  try {
    const translations = await requestTranslations([normalizedText], target, source);
    return translations[0] || "";
  } catch (error) {
    return `[translation failed: ${error.message || error}]`;
  }
}

async function translateRange(texts, targetLanguage, sourceLanguage) {
  const matrix = normalizeMatrix(texts);
  const target = normalizeLanguage(targetLanguage);
  const source = normalizeLanguage(sourceLanguage, "auto");

  if (!target) {
    return [["[translation failed: target language is required]"]];
  }

  const flatTexts = [];
  const positions = [];
  const output = matrix.map((row) => row.map(() => ""));

  matrix.forEach((row, rowIndex) => {
    row.forEach((value, columnIndex) => {
      const normalizedText = normalizeScalar(value);
      if (!normalizedText) {
        output[rowIndex][columnIndex] = "";
        return;
      }

      flatTexts.push(normalizedText);
      positions.push([rowIndex, columnIndex]);
    });
  });

  if (!flatTexts.length) {
    return output;
  }

  try {
    const translations = await requestTranslations(flatTexts, target, source);
    translations.forEach((value, index) => {
      const [rowIndex, columnIndex] = positions[index];
      output[rowIndex][columnIndex] = value;
    });
    return output;
  } catch (error) {
    return [[`[translation failed: ${error.message || error}]`]];
  }
}

async function requestTranslations(texts, targetLanguage, sourceLanguage) {
  const chunks = chunkArray(texts, 64);
  const results = [];

  for (const chunk of chunks) {
    const response = await fetch("/api/translate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        provider: "lm_studio",
        sourceLanguage,
        targetLanguage,
        texts: chunk,
      }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "The translation service returned an error.");
    }

    if (!Array.isArray(data.translations)) {
      throw new Error("Unexpected translation response format.");
    }

    results.push(...data.translations.map((value) => normalizeScalar(value)));
  }

  return results;
}

function normalizeLanguage(value, fallback = "") {
  if (value === null || value === undefined) {
    return fallback;
  }

  const normalized = String(value).trim();
  return normalized || fallback;
}

function normalizeScalar(value) {
  if (value === null || value === undefined) {
    return "";
  }

  return String(value).trim();
}

function normalizeMatrix(value) {
  if (Array.isArray(value)) {
    return value.map((row) => (Array.isArray(row) ? row : [row]));
  }

  return [[value]];
}

function chunkArray(values, chunkSize) {
  const chunks = [];
  for (let index = 0; index < values.length; index += chunkSize) {
    chunks.push(values.slice(index, index + chunkSize));
  }
  return chunks;
}

CustomFunctions.associate("TRANSLATE", translate);
CustomFunctions.associate("TRANSLATE_RANGE", translateRange);
