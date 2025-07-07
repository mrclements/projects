import axios from 'axios';

export const api = axios.create({
  // eslint-disable-next-line @typescript-eslint/strict-boolean-expressions
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:4000',
  headers: { 'Content-Type': 'application/json' }
});
