import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { C } from '../../theme';
import { Field, Btn, Choice } from '../../components/ui';
import { api, errorText } from '../../api';
import StepHeader from './StepHeader';

// Driver step: pick the vehicle type and type the number plate.
// The backend checks the plate format (like MH12AB1234) and that it is not already registered.
export default function VehicleScreen({ index, total, onDone }) {
  const [vehicleType, setVehicleType] = useState('');
  const [plate, setPlate] = useState('');
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  const validate = () => {
    const errs = {};
    if (!vehicleType) errs.type = 'Please choose your vehicle type';
    const clean = plate.toUpperCase().replace(/[\s-]/g, '');
    if (!/^[A-Z]{2}[0-9]{2}[A-Z]{1,3}[0-9]{4}$/.test(clean)) {
      errs.plate = 'Enter a valid vehicle number, like MH12AB1234';
    }
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async () => {
    if (!validate()) return;
    setLoading(true);
    try {
      await api.post('/profile/vehicle', {
        vehicle_type: vehicleType,
        plate_number: plate,
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
      <Text style={s.title}>Your vehicle</Text>
      <Text style={s.subtitle}>Tell us what you will be driving</Text>

      <Text style={s.label}>Vehicle type</Text>
      <Choice
        value={vehicleType}
        onChange={setVehicleType}
        options={['cab', 'auto', 'bike']}
      />
      {errors.type ? <Text style={s.error}>{errors.type}</Text> : null}

      <View style={s.plateWrap}>
        <Field
          label="Vehicle number"
          value={plate}
          onChangeText={(v) => setPlate(v.toUpperCase())}
          placeholder="MH12AB1234"
          autoCapitalize="characters"
          autoCorrect={false}
        />
      </View>
      {errors.plate ? <Text style={s.error}>{errors.plate}</Text> : null}
      {errors.server ? <Text style={s.error}>{errors.server}</Text> : null}

      <View style={s.submitWrap}>
        <Btn title="Continue" onPress={handleSubmit} loading={loading} />
      </View>
    </ScrollView>
  );
}

const s = StyleSheet.create({
  container: { flexGrow: 1, padding: 20, paddingTop: 56, backgroundColor: C.bg },
  title: { fontSize: 28, fontWeight: '800', color: C.text, marginBottom: 8 },
  subtitle: { fontSize: 16, color: C.muted, marginBottom: 24 },
  label: { color: C.muted, fontSize: 13, marginBottom: 8 },
  plateWrap: { marginTop: 16 },
  error: { color: '#FF4444', fontSize: 14, marginBottom: 12, marginTop: 4 },
  submitWrap: { marginBottom: 24 },
});
