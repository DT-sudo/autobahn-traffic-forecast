import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const RAW_DATA_PATH = path.resolve(__dirname, '../../data/raw');

/**
 * Analyze a dataset file from backend/data/raw/.
 * Adapt this function to the specific hackathon theme.
 */
export async function analyzeDataset(filename, analysisType = 'summary') {
  const filePath = path.join(RAW_DATA_PATH, filename);

  if (!fs.existsSync(filePath)) {
    throw new Error(`Dataset not found: ${filename}`);
  }

  const ext = path.extname(filename).toLowerCase();

  if (ext === '.json') {
    return analyzeJson(filePath, analysisType);
  }

  if (ext === '.csv') {
    return analyzeCsv(filePath, analysisType);
  }

  throw new Error(`Unsupported file type: ${ext}`);
}

async function analyzeJson(filePath, analysisType) {
  const raw = fs.readFileSync(filePath, 'utf8');
  const data = JSON.parse(raw);
  const records = Array.isArray(data) ? data : [data];

  return {
    format: 'json',
    rowCount: records.length,
    columns: records.length > 0 ? Object.keys(records[0]) : [],
    sample: analysisType === 'detailed' ? records.slice(0, 5) : undefined,
    insights: [],
  };
}

async function analyzeCsv(filePath, analysisType) {
  const { default: csvParser } = await import('csv-parser');
  const records = [];

  await new Promise((resolve, reject) => {
    fs.createReadStream(filePath)
      .pipe(csvParser())
      .on('data', (row) => records.push(row))
      .on('end', resolve)
      .on('error', reject);
  });

  return {
    format: 'csv',
    rowCount: records.length,
    columns: records.length > 0 ? Object.keys(records[0]) : [],
    sample: analysisType === 'detailed' ? records.slice(0, 5) : undefined,
    insights: [],
  };
}
