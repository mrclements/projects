const express = require('express');
const router = express.Router();
const Joi = require('joi');
const logger = require('../utils/logger');
const axios = require('axios');

// Validation schema
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

// Helper: normalize incoming request body
function normalizeIngestBody(raw) {
  return {
    youtubeUrl: raw.youtubeUrl || raw.youtube_url,
    userConsent: raw.userConsent ?? raw.user_consent
  };
}

// POST /api/analysis/ingest
router.post('/ingest', async (req, res) => {
  logger.info('REQUEST BODY RECEIVED', req.body);

  const transformed = normalizeIngestBody(req.body);
  logger.info('NORMALIZED BODY', transformed);

  const { error, value } = ingestSchema.validate(transformed);
  if (error) {
    logger.error('Validation failed', error.details);
    return res.status(400).json({ error: 'Validation failed', details: error.details });
  }

  logger.info('Ingesting YouTube URL', value);

  try {
    const payload = {
      youtube_url: value.youtubeUrl,
      user_consent: value.userConsent
    };
    logger.info('Forwarding to Analysis Service', payload);

    const ingestResp = await axios.post(
      `${process.env.ANALYSIS_SERVICE_URL}/ingest`,
      payload
    );

    logger.info('Analysis service response', ingestResp.data);
    return res.status(ingestResp.status).json(ingestResp.data);
  } catch (err) {
    logger.error('Error proxying ingest request', err);
    return res.status(502).json({ error: 'Failed to proxy ingest request', message: err.message });
  }
});

// GET /api/analysis/status/:jobId
router.get('/status/:jobId', async (req, res) => {
  const { jobId } = req.params;
  logger.info('Checking job status', { jobId });

  try {
    const statusResp = await axios.get(`${process.env.ANALYSIS_SERVICE_URL}/status/${jobId}`);
    logger.info('Status service response', statusResp.data);
    return res.status(statusResp.status).json(statusResp.data);
  } catch (err) {
    logger.error('Error proxying status request', err);
    return res.status(502).json({ error: 'Failed to proxy status request', message: err.message });
  }
});

// POST /api/analysis/analyze
router.post('/analyze', async (req, res) => {
  logger.info('ANALYZE BODY RECEIVED', req.body);

  const { error, value } = analyzeSchema.validate(req.body);
  if (error) {
    logger.error('Validation failed', error.details);
    return res.status(400).json({ error: 'Validation failed', details: error.details });
  }

  logger.info('Starting analysis', value);

  try {
    const payload = {
      job_id: value.jobId,
      start_time: value.startTime,
      end_time: value.endTime
    };
    logger.info('Forwarding to Analysis Service', payload);

    const analyzeResp = await axios.post(
      `${process.env.ANALYSIS_SERVICE_URL}/analyze`,
      payload
    );

    logger.info('Analysis service response', analyzeResp.data);
    return res.status(analyzeResp.status).json(analyzeResp.data);
  } catch (err) {
    logger.error('Error proxying analyze request', err);
    return res.status(502).json({ error: 'Failed to proxy analyze request', message: err.message });
  }
});

// GET /api/analysis/analysis/:jobId
router.get('/analysis/:jobId', async (req, res) => {
  const { jobId } = req.params;
  logger.info('Fetching analysis results', { jobId });

  try {
    const analysisResp = await axios.get(`${process.env.ANALYSIS_SERVICE_URL}/analysis/${jobId}`);
    logger.info('Analysis service response', analysisResp.data);
    return res.status(analysisResp.status).json(analysisResp.data);
  } catch (err) {
    logger.error('Error proxying analysis request', err);
    return res.status(502).json({ error: 'Failed to proxy analysis request', message: err.message });
  }
});

// GET /api/analysis/audio/:jobId
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
