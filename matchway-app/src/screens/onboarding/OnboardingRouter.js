import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { C } from '../../theme';
import DetailsScreen from './DetailsScreen';
import DocumentScreen from './DocumentScreen';
import SelfieScreen from './SelfieScreen';
import VehicleScreen from './VehicleScreen';
import StatusScreen from '../StatusScreen';

const STUDENT_ORDER = ['details', 'college_id', 'selfie'];
const DRIVER_ORDER = ['details', 'aadhaar', 'pan', 'licence', 'vehicle', 'rc', 'vehicle_photo'];

export default function OnboardingRouter({ profile, onRefresh, onSignOut }) {
  if (!profile || !profile.profile) {
    return (
      <StatusScreen
        title="Setting up your account"
        message="One moment..."
        onSignOut={onSignOut}
        onRefresh={onRefresh}
      />
    );
  }
  const role = profile.profile.role;
  const order = role === 'student' ? STUDENT_ORDER : DRIVER_ORDER;
  const step = profile.next_step;
  const index = order.indexOf(step) + 1;
  const total = order.length;

  const renderStep = () => {
    if (step === 'details') {
      return <DetailsScreen index={index} total={total} onDone={onRefresh} />;
    }
    if (step === 'college_id') {
      return (
        <DocumentScreen
          index={index} total={total} onDone={onRefresh}
          title="Upload your college ID"
          subtitle="Take a clear photo of the front of your ID card"
          docType="college_id"
          tips={['Make sure your name and photo are readable', 'Avoid glare and shadows']}
          needsNumber={false}
        />
      );
    }
    if (step === 'selfie') {
      return <SelfieScreen index={index} total={total} onDone={onRefresh} />;
    }
    if (step === 'aadhaar') {
      // Photo only. The backend rejects an Aadhaar number, so needsNumber stays false.
      // key={step} makes React start with a fresh screen for each document step.
      return (
        <DocumentScreen
          key={step}
          index={index} total={total} onDone={onRefresh}
          title="Upload your Aadhaar card"
          subtitle="Take a clear photo of the front of your Aadhaar card"
          docType="aadhaar"
          tips={[
            'Make sure your name and photo are readable',
            'Avoid glare and shadows',
            'We only need the photo. You do not need to type your Aadhaar number',
          ]}
          needsNumber={false}
        />
      );
    }

    if (step === 'pan') {
      // Photo plus a typed PAN. The backend uppercases it and checks the ABCDE1234F format.
      return (
        <DocumentScreen
          key={step}
          index={index} total={total} onDone={onRefresh}
          title="Upload your PAN card"
          subtitle="Take a clear photo of the front of your PAN card"
          docType="pan"
          tips={[
            'Make sure your name and PAN number are readable',
            'Avoid glare and shadows',
          ]}
          needsNumber={true}
          numberLabel="PAN number"
          numberPlaceholder="ABCDE1234F"
          numberCapitalize={true}
        />
      );
    }

    if (step === 'licence') {
      // Photo plus a typed licence number. The backend uppercases it and checks the format.
      return (
        <DocumentScreen
          key={step}
          index={index} total={total} onDone={onRefresh}
          title="Upload your driving licence"
          subtitle="Take a clear photo of the front of your driving licence"
          docType="licence"
          tips={[
            'Make sure your name and licence number are readable',
            'Avoid glare and shadows',
          ]}
          needsNumber={true}
          numberLabel="Licence number"
          numberPlaceholder="MH12 20200001234"
          numberCapitalize={true}
        />
      );
    }

    if (step === 'vehicle') {
      return <VehicleScreen index={index} total={total} onDone={onRefresh} />;
    }
    if (step === 'rc') {
      // Photo only. The backend does not ask for a number on the RC.
      return (
        <DocumentScreen
          key={step}
          index={index} total={total} onDone={onRefresh}
          title="Upload your vehicle RC"
          subtitle="Take a clear photo of your vehicle's registration certificate"
          docType="rc"
          tips={[
            'Make sure the vehicle number and your name are readable',
            'Avoid glare and shadows',
          ]}
          needsNumber={false}
        />
      );
    }
    if (step === 'vehicle_photo') {
      // Photo only.
      return (
        <DocumentScreen
          key={step}
          index={index} total={total} onDone={onRefresh}
          title="Photo of your vehicle"
          subtitle="Take a clear photo of your vehicle from the front or side"
          docType="vehicle_photo"
          tips={[
            'Show the whole vehicle',
            'Make sure the number plate is visible',
            'Take it in good light',
          ]}
          needsNumber={false}
        />
      );
    }

    return (
      <StatusScreen
        title={`Next: ${step}`}
        message="This screen is coming next."
      />
    );
  };

  return (
    <View style={s.container}>
      <TouchableOpacity style={s.signOutBtn} onPress={onSignOut}>
        <Text style={s.signOutText}>Sign out</Text>
      </TouchableOpacity>
      {renderStep()}
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: C.bg },
  signOutBtn: {
    position: 'absolute',
    top: 56,
    right: 20,
    zIndex: 10
  },
  signOutText: { color: C.yellow, fontSize: 16, fontWeight: '600' },
});