import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { C } from '../../theme';
import { Field, Btn, Choice } from '../../components/ui';
import { api, errorText } from '../../api';
import StepHeader from './StepHeader';

export default function DetailsScreen({ index, total, onDone }) {
  const [form, setForm] = useState({
    full_name: '',
    phone: '',
    gender: '',
    day: '',
    month: '',
    year: '',
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  const validate = () => {
    const errs = {};
    if (form.full_name.trim().length < 2) errs.full_name = 'Name must be at least 2 characters';
    if (!/^\d{10}$/.test(form.phone)) errs.phone = 'Phone must be exactly 10 digits';
    if (!form.gender) errs.gender = 'Please select gender';

    const d = parseInt(form.day);
    const m = parseInt(form.month);
    const y = parseInt(form.year);
    const date = new Date(y, m - 1, d);
    if (isNaN(d) || isNaN(m) || isNaN(y) ||
        date.getFullYear() !== y || date.getMonth() !== m - 1 || date.getDate() !== d) {
      errs.date = 'Please enter a valid date';
    }

    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async () => {
    if (!validate()) return;
    setLoading(true);
    try {
      const dateStr = `${form.year}-${form.month.padStart(2, '0')}-${form.day.padStart(2, '0')}`;
      await api.post('/profile/details', {
        full_name: form.full_name.trim(),
        phone: form.phone.trim(),
        gender: form.gender,
        date_of_birth: dateStr,
      });
      onDone();
    } catch (e) {
      setErrors({ server: errorText(e) });
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView contentContainerStyle={s.container}>
      <StepHeader index={index} total={total} />
      <Text style={s.title}>Tell us about you</Text>
      <Text style={s.subtitle}>These details are shown to your co-riders</Text>

      <Field
        label="Full name"
        value={form.full_name}
        onChangeText={v => setForm({...form, full_name: v})}
        placeholder="John Doe"
      />
      {errors.full_name && <Text style={s.error}>{errors.full_name}</Text>}

      <Field
        label="Phone number"
        value={form.phone}
        onChangeText={v => setForm({...form, phone: v})}
        keyboardType="phone-pad"
        maxLength={10}
        placeholder="9876543210"
      />
      {errors.phone && <Text style={s.error}>{errors.phone}</Text>}

      <Choice
        label="Gender"
        value={form.gender}
        onChange={v => setForm({...form, gender: v})}
        options={['female', 'male']}
      />
      {errors.gender && <Text style={s.error}>{errors.gender}</Text>}

      <Text style={s.label}>Date of birth</Text>
      <View style={s.dateRow}>
        <View style={s.dateCol}>
          <Text style={s.dateLabel}>Day</Text>
          <Field value={form.day} onChangeText={v => setForm({...form, day: v})} keyboardType="numeric" maxLength={2} placeholder="DD" />
        </View>
        <View style={s.dateCol}>
          <Text style={s.dateLabel}>Month</Text>
          <Field value={form.month} onChangeText={v => setForm({...form, month: v})} keyboardType="numeric" maxLength={2} placeholder="MM" />
        </View>
        <View style={s.dateCol}>
          <Text style={s.dateLabel}>Year</Text>
          <Field value={form.year} onChangeText={v => setForm({...form, year: v})} keyboardType="numeric" maxLength={4} placeholder="YYYY" />
        </View>
      </View>
      {errors.date && <Text style={s.error}>{errors.date}</Text>}
      {errors.server && <Text style={s.error}>{errors.server}</Text>}

      <Btn title="Continue" onPress={handleSubmit} loading={loading} />
    </ScrollView>
  );
}

const s = StyleSheet.create({
  container: { flexGrow: 1, padding: 20, paddingTop: 56, backgroundColor: C.bg },
  title: { fontSize: 28, fontWeight: '800', color: C.text, marginBottom: 8 },
  subtitle: { fontSize: 16, color: C.muted, marginBottom: 24 },
  label: { color: C.text, fontSize: 16, marginBottom: 8, marginTop: 16 },
  dateRow: { flexDirection: 'row', gap: 12, marginBottom: 8 },
  dateCol: { flex: 1 },
  dateLabel: { color: C.muted, fontSize: 12, marginBottom: 4 },
  error: { color: '#FF4444', fontSize: 14, marginBottom: 12, marginTop: 4 },
});
