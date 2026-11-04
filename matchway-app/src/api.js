import axios from 'axios';
import { API } from './config';
import { supabase } from './supabase';

export const api = axios.create({
  baseURL: API,
  timeout: 20000,
});

api.interceptors.request.use(async (config) => {
  const { data } = await supabase.auth.getSession();
  if (data.session) {
    config.headers.Authorization = `Bearer ${data.session.access_token}`;
  }
  return config;
});

export function errorText(e) {
  const d = e?.response?.data?.detail;
  if (typeof d === 'string') return d;
  if (Array.isArray(d)) return d.map((x) => x.msg).join('\n');
  return e.message || 'Something went wrong';
}
