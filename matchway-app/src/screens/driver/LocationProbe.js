// A hidden 2x2 WebView that asks Android's web engine for the position.
// This uses the same location service as Chrome and Google Maps, so it works
// even when the app's own location library gets no answer.
import React from 'react';
import { WebView } from 'react-native-webview';
import { API } from '../../config';

const HTML = `<!DOCTYPE html><html><body><script>
function send(o){ if (window.ReactNativeWebView) window.ReactNativeWebView.postMessage(JSON.stringify(o)); }
function fix(p){ send({ t: 'fix', lat: p.coords.latitude, lon: p.coords.longitude }); }
function bad(e){ send({ t: 'err', msg: 'web code ' + e.code + ' ' + e.message }); }
if (!navigator.geolocation) { send({ t: 'err', msg: 'web: no geolocation' }); }
else {
  send({ t: 'err', msg: 'web: asking...' });
  navigator.geolocation.getCurrentPosition(fix, bad, { enableHighAccuracy: false, timeout: 20000, maximumAge: 120000 });
  navigator.geolocation.watchPosition(fix, bad, { enableHighAccuracy: true, maximumAge: 5000 });
}
</script></body></html>`;

export default function LocationProbe({ onFix, onNote }) {
  return (
    <WebView
      originWhitelist={['*']}
      source={{ html: HTML, baseUrl: API }}
      javaScriptEnabled
      geolocationEnabled
      onMessage={(e) => {
        try {
          const m = JSON.parse(e.nativeEvent.data);
          if (m.t === 'fix') onFix(m.lat, m.lon);
          else if (m.t === 'err') onNote(m.msg);
        } catch (err) { /* ignore */ }
      }}
      style={{ position: 'absolute', top: 0, left: 0, width: 2, height: 2, opacity: 0.01 }}
      pointerEvents="none"
    />
  );
}
