// ---- Backend URL -----------------------------------------------------------
// After you deploy the FastAPI backend (Render / Railway / etc.), paste its
// https URL here, e.g. 'https://matchway-api.onrender.com'. With this set,
// the app works on any phone or emulator with no IP address needed.
const HOSTED_API = '';

// Used when HOSTED_API is empty: the Android emulator's alias for the PC that
// runs the emulator, so `uvicorn` on your own PC works without any IP.
// (Real phone over USB: run `adb reverse tcp:8000 tcp:8000` and change this
// to 'http://localhost:8000'.)
const EMULATOR_API = 'http://10.0.2.2:8000';

export const API = HOSTED_API || EMULATOR_API;

// ---- Supabase (replaces the old .env / EXPO_PUBLIC_* values) ---------------
// The anon key is designed to be public, so it is safe to keep in the app.
// Never put the service_role key here.
export const SUPABASE_URL = 'https://wquzwvvvfkwulgjhxrbd.supabase.co';
export const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndxdXp3dnZ2Zmt3dWxnamh4cmJkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODc4Mzk4MzEsImV4cCI6MjEwMzQxNTgzMX0.auha6WuAuQnT4EqlrcWh1KcleUGr1hVe7H0SyxfySh4';

export const STUDENT_DOMAINS = ['college.edu.in','vit.edu'];
export const CODE_LENGTH = 6;
