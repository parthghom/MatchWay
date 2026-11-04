import { Linking, AppState } from 'react-native';
import { supabase } from './supabase';

// Must match the intent-filter in android/app/src/main/AndroidManifest.xml
// and be listed under Supabase > Authentication > URL Configuration > Redirect URLs.
const REDIRECT_TO = 'matchway://auth-callback';

// Opens the browser and waits for matchway://auth-callback to come back.
// Resolves with the returned URL, or null if the user came back without finishing.
function waitForCallback(url) {
  return new Promise((resolve) => {
    let done = false;
    let timer = null;
    const finish = (value) => {
      if (done) return;
      done = true;
      if (timer) clearTimeout(timer);
      linkSub.remove();
      appSub.remove();
      resolve(value);
    };
    const linkSub = Linking.addEventListener('url', ({ url: u }) => {
      if (u && u.startsWith(REDIRECT_TO)) finish(u);
    });
    let left = false;
    const appSub = AppState.addEventListener('change', (state) => {
      if (state !== 'active') {
        left = true;
      } else if (left) {
        // Back in the app: give the deep link a moment to arrive, else treat as cancelled.
        timer = setTimeout(() => finish(null), 1500);
      }
    });
    Linking.openURL(url).catch(() => finish(null));
  });
}

function parseAuthUrl(url) {
  const out = {};
  const hashIndex = url.indexOf('#');
  const beforeHash = hashIndex === -1 ? url : url.slice(0, hashIndex);
  const hash = hashIndex === -1 ? '' : url.slice(hashIndex + 1);
  const query = beforeHash.includes('?') ? beforeHash.split('?')[1] : '';
  [query, hash].join('&').split('&').forEach((pair) => {
    if (!pair) return;
    const i = pair.indexOf('=');
    const k = decodeURIComponent(i === -1 ? pair : pair.slice(0, i));
    const v = i === -1 ? '' : decodeURIComponent(pair.slice(i + 1).replace(/\+/g, ' '));
    out[k] = v;
  });
  return out;
}

// Returns true when signed in, false when the user cancelled. Throws on errors.
export async function signInWithGoogle() {
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: { redirectTo: REDIRECT_TO, skipBrowserRedirect: true, queryParams: { prompt: 'select_account' } },
  });
  if (error) throw error;
  const returnedUrl = await waitForCallback(data.url);
  if (!returnedUrl) return false;
  const p = parseAuthUrl(returnedUrl);
  if (p.error_description) throw new Error(p.error_description);
  if (p.code) {
    const { error: e1 } = await supabase.auth.exchangeCodeForSession(p.code);
    if (e1) throw e1;
    return true;
  }
  if (p.access_token && p.refresh_token) {
    const { error: e2 } = await supabase.auth.setSession({
      access_token: p.access_token,
      refresh_token: p.refresh_token,
    });
    if (e2) throw e2;
    return true;
  }
  throw new Error('Google sign-in did not return a session. Check the redirect URL in Supabase.');
}