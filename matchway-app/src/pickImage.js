import { PermissionsAndroid, Platform } from 'react-native';
import { launchCamera, launchImageLibrary } from 'react-native-image-picker';

// The manifest lists the CAMERA permission, so Android needs us to ask for it
// ourselves before opening the camera (the picker library will not do it).
async function askCameraPermission() {
  if (Platform.OS !== 'android') return true;
  const res = await PermissionsAndroid.request(PermissionsAndroid.PERMISSIONS.CAMERA);
  return res === PermissionsAndroid.RESULTS.GRANTED;
}

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
    if (!(await askCameraPermission())) {
      throw new Error('Camera permission is needed. Allow it in your phone settings.');
    }
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
