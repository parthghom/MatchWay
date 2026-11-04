import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView } from 'react-native';
import { C } from '../theme';
import { Field, Btn, CodeInput } from '../components/ui';
import { supabase } from '../supabase';
import { STUDENT_DOMAINS, CODE_LENGTH } from '../config';
import { signInWithGoogle } from '../googleAuth';

export default function LoginScreen({ role, onBack }) {
  const [step, setStep] = useState('choose');
  const [email, setEmail] = useState('');
  const [token, setToken] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [timer, setTimer] = useState(0);

  useEffect(() => {
    let interval;
    if (timer > 0) {
      interval = setInterval(() => setTimer(t => t - 1), 1000);
    }
    return () => clearInterval(interval);
  }, [timer]);

  const handleGoogleSignIn = async () => {
    setError('');
    setLoading(true);
    try {
      const success = await signInWithGoogle();
      if (!success) {
        setLoading(false);
      }
    } catch (e) {
      setError(e.message);
      setLoading(false);
    }
  };

  const handleSendCode = async () => {
    setError('');
    if (!email.trim()) {
      setError('Email is required');
      return;
    }

    if (role === 'student') {
      const domain = email.toLowerCase().split('@')[1];
      if (!STUDENT_DOMAINS.includes(domain)) {
        setError('Students must use their college email');
        return;
      }
    }

    setLoading(true);
    try {
      await supabase.auth.signInWithOtp({
        email: email.trim(),
        options: { shouldCreateUser: true }
      });
      setStep(1);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async () => {
    setError('');
    setLoading(true);
    try {
      await supabase.auth.verifyOtp({
        email: email.trim(),
        token,
        type: 'email'
      });
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setError('');
    setLoading(true);
    try {
      await supabase.auth.signInWithOtp({
        email: email.trim(),
        options: { shouldCreateUser: true }
      });
      setTimer(30);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView contentContainerStyle={s.container}>
      <View style={s.header}>
        <TouchableOpacity
          onPress={() => {
            if (step === 'choose') onBack();
            else if (step === 1) setStep('choose');
            else setStep(1);
          }}
          style={s.backBtn}
        >
          <Text style={s.backText}>←</Text>
        </TouchableOpacity>
        <Text style={s.title}>
          {step === 'choose' ? 'Sign in' : step === 1 ? 'Sign in' : 'Enter the code'}
        </Text>
        <Text style={s.subtitle}>
          {step === 'choose'
            ? (role === 'student' ? 'Use the Google account or email your college gave you' : 'Use any Google account or email')
            : step === 1
            ? (role === 'student' ? 'Use your college email' : 'Use your Gmail address')
            : `We sent a ${CODE_LENGTH} digit code to ${email}. Check your spam folder too.`}
        </Text>
      </View>

      {step === 'choose' ? (
        <View>
          <Btn
            title="Continue with Google"
            onPress={handleGoogleSignIn}
            loading={loading}
            style={s.googleBtn}
            labelPrefix={<Text style={s.googleG}>G</Text>}
          />
          <View style={s.divider}>
            <View style={s.line} />
            <Text style={s.dividerText}>or</Text>
            <View style={s.line} />
          </View>
          <Btn
            title="Continue with email"
            onPress={() => setStep(1)}
            variant="ghost"
          />
          {error ? <Text style={s.error}>{error}</Text> : null}
        </View>
      ) : step === 1 ? (
        <View>
          <Field
            label="Email"
            value={email}
            onChangeText={setEmail}
            keyboardType="email-address"
            autoCapitalize="none"
            placeholder="email@example.com"
          />
          {error ? <Text style={s.error}>{error}</Text> : null}
          <Btn title="Send code" onPress={handleSendCode} loading={loading} />
        </View>
      ) : (
        <View>
          <CodeInput value={token} onChange={setToken} length={CODE_LENGTH} />
          {error ? <Text style={s.error}>{error}</Text> : null}
          <Btn title="Verify" onPress={handleVerify} loading={loading} />

          <View style={s.footer}>
            <TouchableOpacity
              onPress={handleResend}
              disabled={timer > 0}
            >
              <Text style={[s.link, timer > 0 && { opacity: 0.5 }]}>
                {timer > 0 ? `Resend code in ${timer}s` : 'Resend code'}
              </Text>
            </TouchableOpacity>

            <TouchableOpacity onPress={() => setStep(1)}>
              <Text style={s.link}>Change email</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}
    </ScrollView>
  );
}

const s = StyleSheet.create({
  container: { flexGrow: 1, padding: 20, paddingTop: 56, backgroundColor: C.bg },
  header: { marginBottom: 32 },
  backBtn: { marginBottom: 16 },
  backText: { color: C.yellow, fontSize: 24 },
  title: { fontSize: 28, fontWeight: '800', color: C.text },
  subtitle: { fontSize: 16, color: C.muted, marginTop: 8 },
  error: { color: '#FF4444', fontSize: 14, marginBottom: 12, marginTop: 4, textAlign: 'center' },
  footer: { marginTop: 24, alignItems: 'center' },
  link: { color: C.yellow, fontSize: 15, marginVertical: 8 },
  googleBtn: { backgroundColor: C.yellow },
  googleG: { fontWeight: 'bold', marginRight: 8 },
  divider: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 24
  },
  line: {
    flex: 1,
    height: 1,
    backgroundColor: C.muted,
    opacity: 0.3
  },
  dividerText: {
    color: C.muted,
    marginHorizontal: 10,
    fontSize: 14
  },
});
