const express = require('express');
const router = express.Router();
const Joi = require('joi');
const logger = require('../utils/logger');
const axios = require('axios');

// Validation schemas
const ingestSchema = Joi.object({
  youtubeUrl: Joi.string().uri().required(),
  userConsent: Joi.boolean().valid(true).required()
});

const analyzeSchema = Joi.object({
  jobId: Joi.string().required(),
  startTime: Joi.number().min(0).required(),
  endTime: Joi.number().min(0).required()
}).custom((value, helpers) => {
  if (value.endTime <= value.startTime) {
    return helpers.error('any.invalid');
  }
  return value;
});

// POST /api/analysis/ingest - Submit YouTube URL for processing
router.post('/ingest', async (req, res) => {
  const { error, value } = ingestSchema.validate(req.body);
  if (error) {
    return res.status(400).json({ error: 'Validation failed', details: error.details });
  }

  const { youtubeUrl, userConsent } = value;
  logger.info('Ingesting YouTube URL', { youtubeUrl, userConsent });

  try {
    const ingestResp = await axios.post(
      `${process.env.ANALYSIS_SERVICE_URL}/ingest`,
      { youtube_url: youtubeUrl, user_consent: userConsent }
    );
    return res.status(ingestResp.status).json(ingestResp.data);
  } catch (err) {
    logger.error('Error proxying ingest request', err);
    return res.status(502).json({ error: 'Failed to proxy ingest request', message: err.message });
  }
});

// GET /api/analysis/status/:jobId - Check job status and get waveform data
router.get('/status/:jobId', async (req, res) => {
  const { jobId } = req.params;
  logger.info('Checking job status', { jobId });

  try {
    const statusResp = await axios.get(`${process.env.ANALYSIS_SERVICE_URL}/status/${jobId}`);
    return res.status(statusResp.status).json(statusResp.data);
  } catch (err) {
    logger.error('Error proxying status request', err);
    return res.status(502).json({ error: 'Failed to proxy status request', message: err.message });
  }
});

// POST /api/analysis/analyze - Analyze trimmed segment
router.post('/analyze', async (req, res) => {
  const { error, value } = analyzeSchema.validate(req.body);
  if (error) {
    return res.status(400).json({ error: 'Validation failed', details: error.details });
  }

  const { jobId, startTime, endTime } = value;
  logger.info('Starting analysis', { jobId, startTime, endTime });

  try {
    const analyzeResp = await axios.post(
      `${process.env.ANALYSIS_SERVICE_URL}/analyze`,
      { job_id: jobId, start_time: startTime, end_time: endTime }
    );
    return res.status(analyzeResp.status).json(analyzeResp.data);
  } catch (err) {
    logger.error('Error proxying analyze request', err);
    return res.status(502).json({ error: 'Failed to proxy analyze request', message: err.message });
  }
});

// GET /api/analysis/analysis/:jobId - Fetch analysis results
router.get('/analysis/:jobId', async (req, res) => {
  const { jobId } = req.params;
  logger.info('Fetching analysis results', { jobId });
  try {
    const analysisResp = await axios.get(`${process.env.ANALYSIS_SERVICE_URL}/analysis/${jobId}`);
    return res.status(analysisResp.status).json(analysisResp.data);
  } catch (err) {
    logger.error('Error proxying analysis request', err);
    return res.status(502).json({ error: 'Failed to proxy analysis request', message: err.message });
  }
});

// GET /api/analysis/audio/:jobId - Stream audio for playback
router.get('/audio/:jobId', async (req, res) => {
  const { jobId } = req.params;
  const { start, end } = req.query;
  logger.info('Streaming audio', { jobId, start, end });

  try {
    const audioResp = await axios.get(
      `${process.env.ANALYSIS_SERVICE_URL}/audio/${jobId}?start=${start}&end=${end}`,
      { responseType: 'stream' }
    );
    res.set(audioResp.headers);
    return audioResp.data.pipe(res);
  } catch (err) {
    logger.error('Error proxying audio request', err);
    return res.status(502).json({ error: 'Failed to proxy audio request', message: err.message });
  }
});

module.exports = router;
