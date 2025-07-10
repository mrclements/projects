const express = require('express');
const router = express.Router();
const Joi = require('joi');
const logger = require('../utils/logger');
const axios = require('axios');
const { v4: uuidv4 } = require('uuid');

// Validation schema
const ingestSchema = Joi.object({
  youtubeUrl: Joi.string().uri().required(),
  userConsent: Joi.boolean().valid(true).required()
});

const analyzeSchema = Joi.object({
  jobId: Joi.string().required(),
  startTime: Joi.number().min(0).required(),
  endTime: Joi.number().min(0).required(),
  // V2 Extensions
  analysisVersion: Joi.string().valid('1.0', '2.0').default('2.0'),
  enableCloudServices: Joi.boolean().default(false),
  cloudOptions: Joi.object({
    sourceSeparation: Joi.boolean().default(false),
    advancedStructure: Joi.boolean().default(false),
    enhancedKeyDetection: Joi.boolean().default(false)
  }).optional()
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
      end_time: value.endTime,
      // V2 Extensions
      analysis_version: value.analysisVersion,
      enable_cloud_services: value.enableCloudServices,
      cloud_options: value.cloudOptions || {}
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

// GET /api/analysis/cloud-status
router.get('/cloud-status', async (req, res) => {
  logger.info('Checking cloud service status');

  try {
    const statusResp = await axios.get(`${process.env.ANALYSIS_SERVICE_URL}/cloud-status`);
    logger.info('Cloud status response', statusResp.data);
    return res.status(statusResp.status).json(statusResp.data);
  } catch (err) {
    logger.error('Error checking cloud service status', err);
    return res.status(502).json({ 
      error: 'Failed to check cloud service status', 
      message: err.message,
      services: {
        demucs: { enabled: false, healthy: false, error: 'Service unavailable' },
        spleeter: { enabled: false, healthy: false, error: 'Service unavailable' },
        colab: { enabled: false, healthy: false, error: 'Service unavailable' },
        render: { enabled: false, healthy: false, error: 'Service unavailable' },
        github_actions: { enabled: false, healthy: false, error: 'Service unavailable' }
      }
    });
  }
});

// POST /api/analysis/wake-spaces
router.post('/wake-spaces', async (req, res) => {
  logger.info('Attempting to wake up Hugging Face spaces');
  
  if (process.env.ENABLE_CLOUD_SERVICES !== 'true') {
    logger.info('Cloud services are disabled, skipping wake-up');
    return res.status(200).json({
      success: false,
      enabled: false,
      message: 'Cloud services are disabled in configuration'
    });
  }
  
  try {
    // Call the analysis service to wake up HF spaces
    const wakeResp = await axios.post(`${process.env.ANALYSIS_SERVICE_URL}/wake-spaces`, {}, {
      headers: {
        'x-huggingface-token': process.env.HUGGINGFACE_API_TOKEN
      },
      timeout: 60000 // 60 seconds timeout for waking up spaces
    });
    
    logger.info('Wake spaces response', wakeResp.data);
    return res.status(wakeResp.status).json({
      ...wakeResp.data,
      success: true
    });
  } catch (err) {
    logger.error('Error waking up Hugging Face spaces', err);
    return res.status(502).json({
      success: false,
      enabled: true,
      error: 'Failed to wake up Hugging Face spaces',
      message: err.message,
      services: {
        demucs: { enabled: true, healthy: false, error: 'Service unavailable or cold start' },
        spleeter: { enabled: true, healthy: false, error: 'Service unavailable or cold start' }
      }
    });
  }
});

// POST /api/analysis/separate-tracks
router.post('/separate-tracks', async (req, res) => {
  const { jobId, audioUrl, model = 'demucs' } = req.body;
  
  if (!jobId || !audioUrl) {
    return res.status(400).json({ 
      success: false, 
      error: 'Missing required parameters' 
    });
  }
  
  logger.info(`Separating audio tracks with ${model === 'demucs' ? 'Demucs v4' : 'Spleeter'}`, { jobId, model });
  
  try {
    // Call the analysis service with the Hugging Face token
    const response = await axios.post(
      `${process.env.ANALYSIS_SERVICE_URL}/separate-tracks`,
      {
        job_id: jobId,
        audio_url: audioUrl,
        model: model // Can be 'demucs' or 'spleeter'
      },
      {
        headers: {
          'x-huggingface-token': process.env.HUGGINGFACE_API_TOKEN
        }
      }
    );
    
    if (response.data && response.data.success) {
      logger.info('Track separation successful', { jobId, model });
      return res.status(200).json(response.data);
    } else {
      logger.warn('Track separation failed in analysis service', response.data);
      return res.status(response.status).json(response.data);
    }
  } catch (err) {
    logger.error('Error in track separation', err);
    return res.status(502).json({
      success: false,
      error: `Failed to process audio with ${model === 'demucs' ? 'Demucs v4' : 'Spleeter'}`,
      message: err.message
    });
  }
});

module.exports = router;
