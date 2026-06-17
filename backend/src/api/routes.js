import { Router } from 'express';
import { analyzeDataset } from '../processors/analyzer.js';

export const router = Router();

// Analyze a dataset file
router.post('/analyze', async (req, res) => {
  try {
    const { filename, analysisType = 'summary' } = req.body;
    if (!filename) {
      return res.status(400).json({ success: false, error: 'filename is required' });
    }
    const results = await analyzeDataset(filename, analysisType);
    res.json({ success: true, results });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
});

// Get latest processed results
router.get('/results', async (req, res) => {
  try {
    res.json({ timestamp: new Date().toISOString(), data: {}, statistics: {} });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
});
