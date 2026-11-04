import * as WebBrowser from 'expo-web-browser';
import Constants from 'expo-constants';
import { supabase } from './supabase';

WebBrowser.maybeCompleteAuthSession();

function makeRedirectTo() {
  const host = Constants.expoConfig && Constants.expoConfig.hostUri;
  if (host) return 'exp://' + host + '/--/auth-callback';
  return 'matchway://auth-callback';
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
  const redirectTo = makeRedirectTo();
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: { redirectTo, skipBrowserRedirect: true, queryParams: { prompt: 'select_account' } },
  });
  if (error) throw error;
  const result = await WebBrowser.openAuthSessionAsync(data.url, redirectTo);
  if (result.type !== 'success') return false;
  const p = parseAuthUrl(result.url);
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