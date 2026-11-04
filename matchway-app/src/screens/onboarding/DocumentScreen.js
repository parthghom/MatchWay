import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, Image, ActivityIndicator } from 'react-native';
import { C } from '../../theme';
import { Field, Btn } from '../../components/ui';
import { api, errorText } from '../../api';
import { pickImage } from '../../pickImage';
import StepHeader from './StepHeader';

export default function DocumentScreen({
  title, subtitle, docType, tips, needsNumber, numberLabel, numberPlaceholder, numberCapitalize, index, total, onDone
}) {
  const [photo, setPhoto] = useState(null);
  const [number, setNumber] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handlePick = async (source) => {
    setError('');
    try {
      const res = await pickImage(source, false);
      if (res) setPhoto(res);
    } catch (e) {
      setError(e.message);
    }
  };

  const handleSubmit = async () => {
    setError('');
    setLoading(true);
    try {
      await api.post('/profile/document', {
        doc_type: docType,
        image_base64: photo.base64,
        doc_number: needsNumber ? number : undefined,
      });
      onDone();
    } catch (e) {
      setError(errorText(e));
    } finally {
      setLoading(false);
    }
  };

  const canSubmit = photo && (!needsNumber || number.trim() !== '');

  return (
    <ScrollView contentContainerStyle={s.container}>
      <StepHeader index={index} total={total} />
      <Text style={s.title}>{title}</Text>
      <Text style={s.subtitle}>{subtitle}</Text>

      <View style={s.card}>
        {photo ? (
          <Image source={{ uri: photo.uri }} style={s.image} resizeMode="contain" />
        ) : (
          <View style={s.placeholder}>
            <Text style={s.placeholderText}>No photo yet</Text>
          </View>
        )}
      </View>

      <View style={s.tipsContainer}>
        {tips.map((tip, i) => (
          <Text key={i} style={s.tip}>• {tip}</Text>
        ))}
      </View>

      <Btn title="Take photo" onPress={() => handlePick('camera')} />
      <Btn title="Choose from gallery" variant="ghost" onPress={() => handlePick('gallery')} />

      {needsNumber && (
        <Field
          label={numberLabel}
          value={number}
          onChangeText={setNumber}
          placeholder={numberPlaceholder}
          autoCapitalize={numberCapitalize ? 'characters' : 'none'}
        />
      )}

      {error ? <Text style={s.error}>{error}</Text> : null}
      {loading ? <ActivityIndicator color={C.yellow} style={s.loader} /> : (
        <Btn title="Upload and continue" onPress={handleSubmit} disabled={!canSubmit} />
      )}
    </ScrollView>
  );
}

const s = StyleSheet.create({
  container: { flexGrow: 1, padding: 20, paddingTop: 56, backgroundColor: C.bg },
  title: { fontSize: 28, fontWeight: '800', color: C.text, marginBottom: 8 },
  subtitle: { fontSize: 16, color: C.muted, marginBottom: 24 },
  card: {
    height: 220,
    borderWidth: 2,
    borderColor: C.yellow,
    borderStyle: 'dashed',
    borderRadius: 12,
    overflow: 'hidden',
    marginBottom: 16,
    backgroundColor: '#1A1A1A'
  },
  image: { width: '100%', height: '100%' },
  placeholder: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  placeholderText: { color: C.muted, fontSize: 16 },
  tipsContainer: { marginBottom: 24 },
  tip: { color: C.muted, fontSize: 14, marginBottom: 4 },
  error: { color: '#FF4444', fontSize: 14, marginBottom: 12, marginTop: 4 },
  loader: { marginVertical: 16 },
});
