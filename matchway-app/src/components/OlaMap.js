// Live Ola map, drawn by MapLibre inside a WebView.
// The page loads its style/tiles from OUR backend (/maps/ola/...), which adds
// the Ola key, so the key never sits inside the app.
//
// The app talks to the page with small messages:
//   app -> page: user dot, fly to, route line, pickup/drop markers
//   page -> app: ready, moved (map centre after a drag), error
import React, { forwardRef, useCallback, useEffect, useImperativeHandle, useRef, useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { WebView } from 'react-native-webview';
import { API } from '../config';
import { C } from '../theme';

const STYLE_PATH = 'tiles/vector/v1/styles/default-dark-standard/style.json';
const DEFAULT_CENTER = { lat: 18.5204, lon: 73.8567 }; // Pune, only until GPS arrives

export function buildHtml(api) {
  return `<!doctype html>
<html><head>
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<link rel="stylesheet" href="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.css">
<style>
  html, body, #map { margin: 0; height: 100%; width: 100%; background: #0B0B0B; }
  .you { width: 18px; height: 18px; border-radius: 9px; background: #FFC800; border: 3px solid #fff;
         box-shadow: 0 0 0 0 rgba(255,200,0,.55); animation: pulse 2s infinite; }
  @keyframes pulse { 70% { box-shadow: 0 0 0 16px rgba(255,200,0,0); } 100% { box-shadow: 0 0 0 0 rgba(255,200,0,0); } }
  .pickup { width: 16px; height: 16px; border-radius: 8px; background: #fff; border: 4px solid #FFC800; }
  .spot { position: relative; width: 24px; height: 24px; border-radius: 7px; background: #FFC800; color: #0B0B0B;
          border: 2px solid #0B0B0B; box-shadow: 0 0 0 2px #FFC800; font: 800 13px/20px sans-serif; text-align: center; }
  .spot .lbl { position: absolute; top: 29px; left: 50%; transform: translateX(-50%); white-space: nowrap; text-align: center;
               font: 700 10px/12px sans-serif; color: #FFC800; text-shadow: 0 0 3px #000, 0 0 3px #000, 0 0 3px #000; }
  .spot .lbl small { display: block; font-weight: 500; color: #fff; }
  .far .spot .lbl { display: none; }
  .drop { width: 18px; height: 18px; background: #FFC800; border: 3px solid #0B0B0B; box-shadow: 0 0 0 2px #FFC800; }
</style>
</head><body><div id="map"></div>
<script src="https://unpkg.com/maplibre-gl@4.7.1/dist/maplibre-gl.js"></script>
<script>
(function () {
  var API = ${JSON.stringify(api.replace(/\/+$/, ''))};
  var STYLE = API + '/maps/ola/${STYLE_PATH}';
  var OLA = /^https:\\/\\/(api|app)\\.olamaps\\.io\\//;
  var queue = [], ready = false, map, userMarker, pickupMarker, dropMarker, spotMarkers = [];

  function send(obj) {
    if (window.ReactNativeWebView) window.ReactNativeWebView.postMessage(JSON.stringify(obj));
  }
  function dot(cls) { var el = document.createElement('div'); el.className = cls; return el; }
  function lngLat(p) { return [p.lon, p.lat]; }

  function setMarker(old, cls, p) {
    if (old) old.remove();
    if (!p) return null;
    return new maplibregl.Marker({ element: dot(cls) }).setLngLat(lngLat(p)).addTo(map);
  }

  function run(c) {
    if (c.t === 'user') {
      if (userMarker) userMarker.setLngLat(lngLat(c));
      else userMarker = new maplibregl.Marker({ element: dot('you') }).setLngLat(lngLat(c)).addTo(map);
    } else if (c.t === 'fly') {
      map.easeTo({ center: [c.lon, c.lat], zoom: c.zoom || map.getZoom(), duration: c.instant ? 0 : 700 });
    } else if (c.t === 'markers') {
      pickupMarker = setMarker(pickupMarker, 'pickup', c.pickup);
      dropMarker = setMarker(dropMarker, 'drop', c.drop);
    } else if (c.t === 'resize') {
      map.resize();
    } else if (c.t === 'spots') {
      spotMarkers.forEach(function (m) { m.remove(); });
      spotMarkers = (c.list || []).map(function (sp) {
        var el = dot('spot');
        var parts = String(sp.name).split(' - ');
        el.innerHTML = 'M<div class="lbl">' + parts[0] + (parts[1] ? '<small></small>' : '') + '</div>';
        if (parts[1]) el.querySelector('small').textContent = parts[1];
        return new maplibregl.Marker({ element: el }).setLngLat([sp.longitude, sp.latitude]).addTo(map);
      });
    } else if (c.t === 'route') {
      var pts = (c.points || []).map(function (p) { return [p[1], p[0]]; });
      map.getSource('route').setData({ type: 'Feature', geometry: { type: 'LineString', coordinates: pts } });
      if (pts.length > 1 && c.fit) {
        var b = new maplibregl.LngLatBounds(pts[0], pts[0]);
        pts.forEach(function (p) { b.extend(p); });
        map.fitBounds(b, { padding: c.pad || 60, duration: 600, maxZoom: 16 });
      }
    }
  }
  window.__cmd = function (c) { if (ready) run(c); else queue.push(c); };

  if (!window.maplibregl) { send({ t: 'error', msg: 'Map engine did not load' }); return; }

  map = new maplibregl.Map({
    container: 'map',
    style: STYLE,
    center: [${DEFAULT_CENTER.lon}, ${DEFAULT_CENTER.lat}],
    zoom: 14,
    attributionControl: false,
    pitchWithRotate: false,
    dragRotate: false,
    transformRequest: function (url) {
      if (OLA.test(url)) return { url: API + '/maps/ola/' + url.replace(OLA, '') };
      return { url: url };
    }
  });
  map.touchZoomRotate.disableRotation();

  map.on('load', function () {
    map.addSource('route', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
    map.addLayer({ id: 'route-casing', type: 'line', source: 'route',
      layout: { 'line-cap': 'round', 'line-join': 'round' },
      paint: { 'line-color': '#0B0B0B', 'line-width': 9 } });
    map.addLayer({ id: 'route-line', type: 'line', source: 'route',
      layout: { 'line-cap': 'round', 'line-join': 'round' },
      paint: { 'line-color': '#FFC800', 'line-width': 5 } });
    ready = true;
    queue.forEach(run);
    queue = [];
    send({ t: 'ready' });
  });
  // college names only show once you zoom in, so the map stays clean
  function farFlag() { document.body.className = map.getZoom() < 14.5 ? 'far' : ''; }
  map.on('zoom', farFlag);
  map.on('load', farFlag);
  map.on('movestart', function (e) { if (e.originalEvent) send({ t: 'movestart' }); });
  map.on('moveend', function () {
    var c = map.getCenter();
    send({ t: 'moved', lat: c.lat, lon: c.lng });
  });
  map.on('error', function (e) {
    var m = e && e.error && e.error.message ? e.error.message : 'map error';
    send({ t: 'error', msg: m });
  });
})();
</script></body></html>`;
}

const OlaMap = forwardRef(function OlaMap(
  { user, route, pickup, drop, spots, visible = true, fitPad, onMoved, onMoveStart, style, children },
  ref
) {
  const web = useRef(null);
  const loaded = useRef(false);
  const centered = useRef(false);
  const [key, setKey] = useState(0);
  const [failed, setFailed] = useState(false);

  const cmd = useCallback((c) => {
    if (web.current) web.current.injectJavaScript(`window.__cmd(${JSON.stringify(c)});true;`);
  }, []);

  useImperativeHandle(ref, () => ({
    flyTo: (lat, lon, zoom, instant) => cmd({ t: 'fly', lat, lon, zoom, instant }),
  }), [cmd]);

  // keep the blue/yellow "you are here" dot on the live GPS position
  useEffect(() => {
    if (!user) return;
    cmd({ t: 'user', lat: user.lat, lon: user.lon });
    if (!centered.current) {
      centered.current = true;
      cmd({ t: 'fly', lat: user.lat, lon: user.lon, zoom: 15, instant: true });
    }
  }, [user, cmd]);

  useEffect(() => {
    cmd({ t: 'markers', pickup: pickup || null, drop: drop || null });
  }, [pickup, drop, cmd]);

  useEffect(() => {
    cmd({ t: 'route', points: route || null, fit: !!route, pad: fitPad });
  }, [route, fitPad, cmd]);

  useEffect(() => {
    cmd({ t: 'spots', list: spots || [] });
  }, [spots, cmd]);

  // the map was hidden (another tab): re-measure it when it comes back
  useEffect(() => {
    if (visible) cmd({ t: 'resize' });
  }, [visible, cmd]);

  function onMessage(e) {
    let m;
    try { m = JSON.parse(e.nativeEvent.data); } catch (err) { return; }
    if (m.t === 'ready') {
      loaded.current = true;
      setFailed(false);
      // the page may have loaded after the first props: send them again
      if (user) cmd({ t: 'user', lat: user.lat, lon: user.lon });
      cmd({ t: 'markers', pickup: pickup || null, drop: drop || null });
      cmd({ t: 'route', points: route || null, fit: !!route, pad: fitPad });
      cmd({ t: 'spots', list: spots || [] });
    } else if (m.t === 'moved') {
      onMoved && onMoved({ lat: m.lat, lon: m.lon });
    } else if (m.t === 'movestart') {
      onMoveStart && onMoveStart();
    } else if (m.t === 'error') {
      console.warn('Map: ' + m.msg);
      // only a missing map engine is fatal; a missing tile or font is not
      if (!loaded.current && /engine/i.test(m.msg)) setFailed(true);
    }
  }

  function retry() {
    loaded.current = false;
    centered.current = false;
    setFailed(false);
    setKey((k) => k + 1);
  }

  return (
    <View style={[s.wrap, style]}>
      <WebView
        key={key}
        ref={web}
        originWhitelist={['*']}
        // baseUrl = our backend, so the page may call it without CORS trouble
        source={{ html: buildHtml(API), baseUrl: API }}
        onMessage={onMessage}
        javaScriptEnabled
        domStorageEnabled
        overScrollMode="never"
        setBuiltInZoomControls={false}
        style={s.web}
        containerStyle={s.web}
        onError={() => setFailed(true)}
        onHttpError={() => setFailed(true)}
      />
      {failed && (
        <View style={s.fail}>
          <Text style={s.failText}>Map could not load. Check your internet and the server.</Text>
          <TouchableOpacity onPress={retry} style={s.retry}>
            <Text style={s.retryText}>Try again</Text>
          </TouchableOpacity>
        </View>
      )}
      {children}
    </View>
  );
});

export default OlaMap;

const s = StyleSheet.create({
  wrap: { flex: 1, backgroundColor: C.bg, overflow: 'hidden' },
  web: { flex: 1, backgroundColor: C.bg },
  fail: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: C.bg,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  failText: { color: C.muted, textAlign: 'center', marginBottom: 14 },
  retry: { borderWidth: 1, borderColor: C.yellow, borderRadius: 12, paddingVertical: 10, paddingHorizontal: 22 },
  retryText: { color: C.yellow, fontWeight: '700' },
});
