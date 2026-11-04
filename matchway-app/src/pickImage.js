import * as ImagePicker from 'expo-image-picker';

// source: 'camera' or 'gallery'; front: true for selfies.
// Returns { uri, base64 } or null if the user cancelled.
export async function pickImage(source, front) {
  const options = { mediaTypes: ['images'], quality: 0.4, base64: true, exif: false };
  if (source === 'camera') {
    const perm = await ImagePicker.requestCameraPermissionsAsync();
    if (!perm.granted) throw new Error('Camera permission is needed. Allow it in your phone settings.');
    if (front) options.cameraType = ImagePicker.CameraType.front;
    const res = await ImagePicker.launchCameraAsync(options);
    if (res.canceled) return null;
    return { uri: res.assets[0].uri, base64: res.assets[0].base64 };
  }
  const perm = await ImagePicker.requestMediaLibraryPermissionsAsync();
  if (!perm.granted) throw new Error('Photo permission is needed. Allow it in your phone settings.');
  const res = await ImagePicker.launchImageLibraryAsync(options);
  if (res.canceled) return null;
  return { uri: res.assets[0].uri, base64: res.assets[0].base64 };
}
