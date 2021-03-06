__author__ = 'Erdene-Ochir Tuguldur'

import random
import numpy as np

import librosa
import python_speech_features as psf


class Compose(object):
    """Composes several transforms together."""

    def __init__(self, transforms):
        self.transforms = transforms

    def __call__(self, data):
        for t in self.transforms:
            data = t(data)
        return data


class LoadAudio(object):
    """Loads an audio into a numpy array."""

    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate

    def __call__(self, data):
        samples, sample_rate = librosa.load(data['fname'], self.sample_rate)
        # audio_duration = len(samples) * 1.0 / sample_rate

        data['samples'] = samples
        data['sample_rate'] = sample_rate

        return data


class SpeedChange(object):
    """Change the speed of an audio. This transform also changes the pitch of the audio."""

    def __init__(self, max_scale=0.2, probability=0.5):
        self.max_scale = max_scale
        self.probability = probability

    def __call__(self, data):
        if random.random() < self.probability:
            samples = data['samples']

            scale = random.uniform(-self.max_scale, self.max_scale)
            speed_fac = 1.0 / (1 + scale)
            data['samples'] = np.interp(np.arange(0, len(samples), speed_fac),
                                        np.arange(0, len(samples)), samples).astype(np.float32)

        return data


class ExtractSpeechFeatures(object):
    """Mel spectrogram."""

    def __init__(self, num_features=64):
        self.num_features = num_features
        self.window_size = 20e-3
        self.window_stride = 10e-3

    def __call__(self, data):
        samples = data['samples']
        sample_rate = data['sample_rate']

        # T, F
        features = psf.logfbank(signal=samples,
                                samplerate=sample_rate,
                                winlen=self.window_size,
                                winstep=self.window_stride,
                                nfilt=self.num_features,
                                nfft=512,
                                lowfreq=0, highfreq=sample_rate / 2,
                                preemph=0.97)
        # normalize
        m = np.mean(features)
        s = np.std(features)
        features = (features - m) / s

        data = {
            'target': data['text'],
            'target_length': len(data['text']),
            'input': features.astype(np.float32),
            'input_length': features.shape[0]
        }

        return data
