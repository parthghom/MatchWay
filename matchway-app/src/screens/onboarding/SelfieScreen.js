import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, Image, ActivityIndicator } from 'react-native';
import { C } from '../../theme';
import { Btn } from '../../components/ui';
import { api, errorText } from '../../api';
import { pickImage } from '../../pickImage';
import StepHeader from './StepHeader';

export default function SelfieScreen({ index, total, onDone }) {
  const [photo, setPhoto] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleTakeSelfie = async () => {
    setError('');
    try {
      const res = await pickImage('camera', true);
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
        doc_type: 'selfie',
        image_base64: photo.base64,
      });
      onDone();
    } catch (e) {
      setError(errorText(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView contentContainerStyle={s.container}>
      <StepHeader index={index} total={total} />
      <Text style={s.title}>Verify your face</Text>
      <Text style={s.subtitle}>Position your face within the oval and make sure there is good lighting</Text>

      <View style={s.ovalContainer}>
        <View style={s.oval}>
          {photo ? (
            <Image source={{ uri: photo.uri }} style={s.image} resizeMode="cover" />
          ) : (
            <Text style={s.emoji}>🙂</Text>
          )}
        </View>
      </View>

      <Text style={s.info}>Your selfie is only used to confirm that it is really you.</Text>

      {!photo ? (
        <Btn title="Take selfie" onPress={handleTakeSelfie} />
      ) : (
        <View style={s.actionRow}>
          <Btn title="Submit selfie" onPress={handleSubmit} loading={loading} />
          <Btn title="Retake" variant="ghost" onPress={handleTakeSelfie} />
        </View>
      )}

      {error ? <Text style={s.error}>{error}</Text> : null}
    </ScrollView>
  );
}

const s = StyleSheet.create({
  container: { flexGrow: 1, padding: 20, paddingTop: 56, backgroundColor: C.bg, alignItems: 'center' },
  title: { fontSize: 28, fontWeight: '800', color: C.text, marginBottom: 8, textAlign: 'center' },
  subtitle: { fontSize: 16, color: C.muted, marginBottom: 32, textAlign: 'center' },
  ovalContainer: { alignItems: 'center', marginBottom: 24 },
  oval: {
    width: 210,
    height: 280,
    borderRadius: 140,
    borderWidth: 3,
    borderColor: C.yellow,
    overflow: 'hidden',
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#1A1A1A'
  },
  image: { width: '100%', height: '100%' },
  emoji: { fontSize: 64 },
  info: { color: C.muted, fontSize: 14, textAlign: 'center', marginBottom: 32 },
  actionRow: { width: '100%', gap: 12 },
  error: { color: '#FF4444', fontSize: 14, marginTop: 16, textAlign: 'center' },
});
