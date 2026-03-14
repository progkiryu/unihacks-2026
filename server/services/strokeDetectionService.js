const tf = require("@tensorflow/tfjs-node");
const Jimp = require("jimp");
const { v4: uuidv4 } = require("uuid");

const MODEL_PATH = "file://./model/model.json"; // path to your model.json + .bin files
let model = null;

/**
 * Loads the model once and caches it.
 */
const loadModel = async () => {
  if (!model) {
    model = await tf.loadLayersModel(MODEL_PATH);
    console.log("Stroke detection model loaded.");
  }
  return model;
};

/**
 * Converts a base64 image into a 224x224 normalised tensor
 * matching the model's expected input shape [1, 224, 224, 3].
 */
const preprocessImage = async (base64Image) => {
  const buffer = Buffer.from(base64Image, "base64");
  const image = await Jimp.read(buffer);

  image.resize(224, 224);

  const pixels = [];
  image.scan(0, 0, 224, 224, (x, y, idx) => {
    pixels.push(image.bitmap.data[idx] / 255);       // R
    pixels.push(image.bitmap.data[idx + 1] / 255);   // G
    pixels.push(image.bitmap.data[idx + 2] / 255);   // B
  });

  return tf.tensor4d(pixels, [1, 224, 224, 3]);
};

/**
 * Maps the raw sigmoid score to a human-readable risk level and recommendation.
 */
const interpretScore = (score) => {
  if (score >= 0.7) return {
    riskLevel: "high",
    recommendation: "High stroke risk detected. Call emergency services (000) immediately.",
  };
  if (score >= 0.4) return {
    riskLevel: "medium",
    recommendation: "Possible stroke indicators. Seek medical attention urgently.",
  };
  return {
    riskLevel: "low",
    recommendation: "No significant stroke indicators detected. Continue monitoring.",
  };
};

// In-memory store — swap for a DB in production
const diagnosisStore = new Map();

exports.analyzeImage = async (base64Image) => {
  const net = await loadModel();
  const tensor = await preprocessImage(base64Image);

  const prediction = net.predict(tensor);
  const score = (await prediction.data())[0]; // single sigmoid output

  tensor.dispose();
  prediction.dispose();

  const { riskLevel, recommendation } = interpretScore(score);

  const record = {
    diagnosisId: uuidv4(),
    timestamp: new Date().toISOString(),
    analysis: {
      score: parseFloat(score.toFixed(4)),  // raw model output e.g. 0.8312
      riskLevel,
      recommendation,
    },
  };

  diagnosisStore.set(record.diagnosisId, record);
  return record;
};

exports.getDiagnosis = (diagnosisId) => {
  if (!diagnosisId) throw new Error("diagnosisId is required");
  const record = diagnosisStore.get(diagnosisId);
  if (!record) throw new Error(`No diagnosis found for id: ${diagnosisId}`);
  return record;
};

