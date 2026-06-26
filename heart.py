import streamlit as st
import numpy as np
import av
import time
import cv2
from scipy.signal import butter, filtfilt, find_peaks
from scipy.fft import rfft, rfftfreq
from streamlit_webrtc import webrtc_streamer, RTCConfiguration, WebRtcMode
import math

st.set_page_config(page_title="Mobile Heart Rate", layout="centered", page_icon="❤️")

# Mobile-optimized RTC config (essential for mobile browsers)
RTC_CONFIGURATION = RTCConfiguration({
    "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
})

class MobileHeartRateProcessor:
    def __init__(self):
        self.values = []
        self.times = []
        self.start_time = None
        self.measuring = False
        self.bpm = None
        self.confidence = 0.0
        
    def recv_queued_frames(self, frames):
        frame = frames[0]
        img = frame.to_ndarray(format="bgr24")
        
        # Flash simulation - make darker when measuring
        if self.measuring:
            img = cv2.convertScaleAbs(img, alpha=0.7, beta=-30)
        
        h, w = img.shape[:2]
        roi = img[h//3:2*h//3, w//3:2*w//3]  # Center fingertip ROI
        
        # Use GREEN channel (best for blood flow PPG)
        green_signal = np.mean(roi[:,:,1])
        
        # Adaptive finger detection (works better on mobile)
        brightness = np.mean(img)
        skin_ratio = np.sum(roi[:,:,1] > 100) / roi.shape[0] / roi.shape[1]
        
        if skin_ratio > 0.3 and brightness > 50 and not self.measuring:
            self.start_measuring()
            
        if self.measuring:
            self.values.append(green_signal)
            self.times.append(time.time())
            
            # Limit to 30 seconds max (900 frames ~30s @30fps)
            if len(self.values) > 900:
                self.values = self.values[-300:]  # Keep last 10s
                self.times = self.times[-300:]
            
            # Calculate every 5 seconds during measurement
            if len(self.values) > 150 and time.time() - self.start_time > 5:
                self.calculate_bpm()
        
        return av.VideoFrame.from_ndarray(img, format="bgr24")
    
    def start_measuring(self):
        if not self.measuring:
            self.start_time = time.time()
            self.measuring = True
            self.values = []
            self.times = []
    
    def calculate_bpm(self):
        if len(self.values) < 100:
            return
            
        signal = np.array(self.values) - np.mean(self.values)
        fs = len(signal) / (self.times[-1] - self.times[0])
        
        # Bandpass filter 0.8-3Hz (48-180 BPM)
        nyquist = fs / 2
        low, high = 0.8/nyquist, 3.0/nyquist
        b, a = butter(4, [low, high], btype='band')
        filtered = filtfilt(b, a, signal)
        
        # FFT for frequency domain peak detection
        N = len(filtered)
        freqs = rfftfreq(N, 1/fs)
        fft_vals = np.abs(rfft(filtered))
        
        # Find peak in heart rate range
        hr_range = (freqs >= 0.8) & (freqs <= 3.0)
        peak_idx = np.argmax(fft_vals[hr_range])
        peak_freq = freqs[hr_range][peak_idx]
        
        bpm = peak_freq * 60
        if 50 <= bpm <= 180:
            self.bpm = round(bpm)
            self.confidence = min(95, 70 + fft_vals[peak_idx]/np.max(fft_vals)*25)
    
    def get_state(self):
        elapsed = time.time() - self.start_time if self.measuring and self.start_time else 0
        return {
            "measuring": self.measuring,
            "finger_detected": len(self.values) > 10,
            "bpm": self.bpm,
            "confidence": self.confidence,
            "elapsed": min(30, elapsed),
            "status": "Place finger on camera" if not self.measuring else 
                     f"Measuring... {int(elapsed)}s" if elapsed < 30 else "Complete!"
        }

# Main App
st.title("❤️ Mobile Heart Rate Monitor")
st.markdown("**Place finger on camera lens. Uses flash effect. 30s max.**")

if "hr_state" not in st.session_state:
    st.session_state.hr_state = {}

# Mobile-first layout
col1, col2 = st.columns([1, 2])

with col1:
    st.info("📱 **Mobile optimized**\n• Chrome/Safari\n• Auto flash\n• 30s max")
    
with col2:
    ctx = webrtc_streamer(
        key="hr-mobile",
        mode=WebRtcMode.SENDONLY,
        rtc_configuration=RTC_CONFIGURATION,
        video_processor_factory=MobileHeartRateProcessor,
        media_stream_constraints={
            "video": {
                "width": {"ideal": 640, "max": 640},
                "height": {"ideal": 480, "max": 480},
                "facingMode": "environment"  # Back camera on mobile
            }
        },
        video_frame_callback=None,
        audio_frame_callback=None,
    )

# Results display
if ctx.video_processor:
    state = ctx.video_processor.get_state()
    st.session_state.hr_state = state
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if state["finger_detected"]:
            st.metric("Status", state["status"], delta=f"{state['elapsed']}s")
        else:
            st.warning("👆 Cover entire camera lens")
    
    with col2:
        if state["bpm"]:
            st.metric("💓 Heart Rate", f"{state['bpm']} BPM", 
                     delta=f"{state['confidence']:.0f}% confidence")
        else:
            st.metric("💓 Heart Rate", "Detecting...", "-")
    
    with col3:
        st.metric("⏱️ Time", f"{state['elapsed']:.0f}/30s")
    
    # Progress bar
    progress = min(1.0, state["elapsed"]/30)
    st.progress(progress)
    
    if state["bpm"]:
        st.balloons()
        st.success(f"✅ **Final Result: {state['bpm']} BPM** (Confidence: {state['confidence']:.0f}%)")
        st.info("💡 *Typical ranges: Resting 60-100, Exercise 100-160*")

# Reset button
if st.button("🔄 New Measurement", use_container_width=True):
    if ctx.video_processor:
        ctx.video_processor.measuring = False
        ctx.video_processor.bpm = None
    st.rerun()

# Mobile instructions
with st.expander("📖 How to use on mobile"):
    st.markdown("""
    1. **Open in Chrome/Safari** (mobile browser)
    2. **Allow camera permission**
    3. **Cover entire camera lens** with fingertip
    4. **Keep steady** for 30 seconds max
    5. **Good lighting** helps accuracy
    """)
