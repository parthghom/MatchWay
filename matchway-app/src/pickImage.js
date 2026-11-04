import { launchCamera, launchImageLibrary } from 'react-native-image-picker';

// source: 'camera' or 'gallery'; front: true for selfies.
// Returns { uri, base64 } or null if the user cancelled.
export async function pickImage(source, front) {
  const options = {
    mediaType: 'photo',
    quality: 0.4,
    includeBase64: true,
    includeExtra: false,
    selectionLimit: 1,
  };
  if (source === 'camera') {
    options.cameraType = front ? 'front' : 'back';
  }
  const res = source === 'camera' ? await launchCamera(options) : await launchImageLibrary(options);
  if (res.didCancel) return null;
  if (res.errorCode === 'permission') {
    throw new Error(
      source === 'camera'
        ? 'Camera permission is needed. Allow it in your phone settings.'
        : 'Photo permission is needed. Allow it in your phone settings.'
    );
  }
  if (res.errorCode) throw new Error(res.errorMessage || 'Could not open the picker.');
  const asset = res.assets && res.assets[0];
  if (!asset) return null;
  return { uri: asset.uri, base64: asset.base64 };
}
