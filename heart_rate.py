import numpy as np
import av
import time
from scipy.signal import find_peaks
from streamlit_webrtc import VideoProcessorBase


class HeartRateProcessor(VideoProcessorBase):

    def __init__(self):
        self.values = []
        self.times = []
        self.start_time = time.time()
        self.bpm = 0

    def recv(self, frame):

        img = frame.to_ndarray(format="bgr24")

        # RED channel average
        red_mean = np.mean(img[:, :, 2])

        current_time = time.time()

        self.values.append(red_mean)
        self.times.append(current_time)

        
        while self.times and current_time - self.times[0] > 20:
            self.times.pop(0)
            self.values.pop(0)

        # Calculate BPM
        if len(self.values) > 50:

            signal = np.array(self.values)
            signal = signal - np.mean(signal)
            signal = np.convolve(signal, np.ones(5)/5, mode='same')

            peaks, _ = find_peaks(signal, distance=8,prominence=0.4)

            duration = self.times[-1] - self.times[0]

            if duration > 5 and len(peaks) > 2:
                self.bpm = int((len(peaks) / duration) * 60)

        return av.VideoFrame.from_ndarray(img, format="bgr24")

    def get_bpm(self):
        return self.bpm
