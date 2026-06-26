import streamlit as st
import joblib
import numpy as np
import pandas as pd
import random
import mysql.connector
from utils.weather import get_weather
from utils.chatbot import chatbot_advice
from tracker import step_tracker
from streamlit_webrtc import webrtc_streamer
from heart_rate import HeartRateProcessor

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Keerthana57",  
        database="walktime_db"
    )

@st.cache_resource
def load_models():
    stress_model = joblib.load("stress_model.pkl")
    walk_model = joblib.load("walk_model.pkl")
    return stress_model, walk_model
stress_model, walk_model = load_models()

if "messages" not in st.session_state:
    st.session_state.messages = []

if "stress" not in st.session_state:
    st.session_state.stress = None

if "page" not in st.session_state:
    st.session_state.page = "main"

@st.cache_data(ttl=600)   
def cached_weather(city):
      return get_weather(city)

def walk_safety_recommendation(temp,humidity):

    if temp > 35:
        return "⚠ Temperature is high. Recommended to walk in the evening or indoor walk."

    elif temp < 18:
        return "❄ Cool weather. Morning walk is perfect."

    elif humidity > 80:
        return "💧 High humidity. You may feel tired quickly or do indoor walk."

    else:
        return "✅ Weather conditions are suitable for walking."

def best_walk_time(temp, humidity):

    if temp >= 35:
        return "🌇 Evening (after 6 PM) is best."

    elif 20 <= temp < 35 and humidity < 80:
        return "🌅 Morning (5 AM - 8 AM) is ideal."

    elif temp < 20:
        return "☀ Late Morning (8 AM - 10 AM) is comfortable."

    elif humidity >= 80:
        return "🌆 Evening is better due to humidity."

    else:
        return "✅ You can walk anytime."
if st.session_state.page == "main":

 st.title("🚶 AI Walking Recommendation System")
 tab1, tab2, tab3, tab4 = st.tabs(
  ["Recommendation","❤️Heart Rate","🚶Tracker","Chatbot"])
 
with tab1:
   st.write("Enter your health details")
   st.divider()

   with st.form("health_form"):
      name = st.text_input("Name")
      email = st.text_input("Email")
      gender = st.selectbox("Gender", ["Male", "Female"])
      col1, col2 = st.columns(2)
      with col1:
        age = st.number_input("Age", 0, 80)
        height = st.number_input("Height (cm)", 0, 220)
        weight = st.number_input("Weight (kg)", 0, 150)
    
      with col2:
        heart = st.number_input("Heart Rate")
        sleep = st.number_input("Sleep Hours")
        steps = st.number_input("Daily Steps")
        city = st.text_input("City Name", "Chennai")
      submit = st.form_submit_button(" 🚀 Get Recommendation")

   if submit:

      with st.spinner("Analyzing your health data... Please wait"):
     
     
        height_m = height / 100
        bmi = weight / (height_m ** 2)

        input_data = pd.DataFrame(
               [[sleep,heart]],
               columns=["Sleep Duration", "Heart Rate"]
        )
        stress = stress_model.predict(input_data)[0]

        temp, humidity = cached_weather(city)
        safety_msg = walk_safety_recommendation(temp, humidity)        
        best_time = best_walk_time(temp, humidity)

        stress_map = {"Low":2, "Medium":5, "High":8}
        stress_num = stress_map.get(stress, 5)

        walk_input = pd.DataFrame(
        [[age, bmi, heart, sleep, stress_num]],
        columns=["age","bmi","avg_heart_rate","hours_sleep","stress_level"]
)
        duration = walk_model.predict(walk_input )[0]
        calories = duration * weight * 0.04
        avg_steps_per_min = 100 if age > 50 else 120
        estimated_steps = int(duration * avg_steps_per_min)

        st.write(f"Calculated BMI: {round(bmi, 2)}")
        
        st.session_state.stress = stress
        st.session_state.temp = temp
        st.session_state.humidity = humidity
        st.session_state.duration = duration
        
      st.session_state.goal_steps = estimated_steps
    
      c1, c2, c3 = st.columns(3)

      c1.metric("Stress Level", stress)
      c2.metric("Temperature", f"{temp}°C")
      c3.metric("Humidity", f"{humidity}%")
      st.subheader("🌤 Smart Walk Safety")

      if "hot" in safety_msg.lower():
             st.warning(safety_msg)
      elif "cool" in safety_msg.lower():
             st.info(safety_msg)
      elif "humidity" in safety_msg.lower():
             st.warning(safety_msg)
      else:
             st.success(safety_msg)
      st.subheader("⏰ Best Time to Walk")
      st.success(best_time)

      st.subheader("🩺 Health Risk Indicator")

      if heart > 110 or stress == "High":
        st.error("⚠ High health stress detected. Try relaxation and light walking.")
      elif heart > 90 or stress == "Medium":
         st.warning("⚡ Moderate stress. Moderate walking recommended.")
      else:
         st.success("✅ Your health indicators look good.")

      

      st.subheader("🚶 Your Walking Plan")

      col1, col2, col3 = st.columns(3)

      with col1:
         st.metric("🚶 Walking Time", f"{round(duration,1)} min")

      with col2:
         st.metric("👣 Steps", estimated_steps)

      with col3:
         st.metric("🔥 Calories Burned", f"{round(calories)} kcal")

         
     
      score = 100

      if stress == "High":
        score -= 30
      elif stress == "Medium":
        score -= 15

      if sleep < 6:
        score -= 20

      if heart > 100:
        score -= 10

      st.metric("⭐ Health Score", f"{score}/100")

      try:
                conn = get_db_connection()
                cursor = conn.cursor()

                cursor.execute("""
                INSERT INTO user (name, age, height, weight, email, gender)
                VALUES (%s, %s, %s, %s, %s, %s)
                """, (name, age, height, weight, email, gender))

                user_id = cursor.lastrowid

                cursor.execute("""
                INSERT INTO health_data1 
                (user_id, heart_rate, sleep_hours, steps, city, bmi, stress_level, temperature, humidity, walking_time, calories)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    user_id, heart, sleep, steps, city,
                    bmi, stress, temp, humidity,
                    duration, calories
                ))

                conn.commit()
                cursor.close()
                conn.close()

                st.success("✅ Data saved to database")

      except Exception as e:
                st.error(f"Database Error: {e}")

      if duration < 20:
        level = "Light Walk"
      elif duration < 40:
        level = "Moderate Walk"
      else:
        level = "Intense Walk"

      st.info(f"🚶 Walking Intensity: {level}")

      progress = min(steps / estimated_steps, 1.0) if estimated_steps > 0 else 0
      st.progress(progress)
      st.write(f"Goal Progress: {int(progress*100)}%")

      steps = st.session_state.get("steps_walked", 0)
      goal = st.session_state.get("goal_steps", 0)


      with st.expander("Health recommended"):
         st.info(chatbot_advice(stress, temp, humidity, duration))
       

      tips = [
        "Drink water before walking 💧",
        "Stretch before walking 🧘",
        "Morning walking improves metabolism ☀️",
        "Slow breathing reduces stress 🌿"
         ]
      with st.expander("💡 View Health Tips"):
       st.info(f"💡 Health Tip: {random.choice(tips)}")

   if st.button("🔄 Clear / New Recommendation"):
    st.session_state.messages = []
    st.session_state.stress = None
    st.session_state.show_result = False
    st.rerun()

with tab2:

    st.header("❤️ Heart Rate Monitor")

    ctx = webrtc_streamer(
        key="heart",
        video_processor_factory=HeartRateProcessor,
        media_stream_constraints={
            "video": {"facingMode": "environment"},
            "audio": False
        },
    )

    if ctx.video_processor:

        import time
        import numpy as np

        progress_bar = st.progress(0)
        status = st.empty()

        status.info("👉 Place your finger on the camera (cover lens + flash)")

        bpm_values = []
        raw_signal = []


        for i in range(12):
            time.sleep(1)
            progress_bar.progress((i + 1) / 12)

            bpm = ctx.video_processor.get_bpm()

            if bpm > 0:
                raw_signal.append(bpm)


            if 50 <= bpm <= 130:
                bpm_values.append(bpm)

        progress_bar.empty()


        def smooth_signal(data, window_size=3):
            if len(data) < window_size:
                return data
            smoothed = []
            for i in range(len(data)):
                window = data[max(0, i-window_size):i+1]
                smoothed.append(sum(window) / len(window))
            return smoothed

        smoothed_values = smooth_signal(bpm_values)


        if len(smoothed_values) > 0:
            final_bpm = int(np.mean(smoothed_values))


            if final_bpm < 60:
                st.warning(f"⚠ Low Heart Rate: {final_bpm} BPM")
            elif final_bpm > 100:
                st.warning(f"⚠ High Heart Rate: {final_bpm} BPM")
            else:
                st.success(f"❤️ Normal Heart Rate: {final_bpm} BPM")

        else:
            st.error("❌ Poor signal. Please adjust finger and try again.")


        if len(smoothed_values) > 0:
            st.subheader("📈 Heart Signal (Smoothed)")
            st.line_chart(smoothed_values)

        with st.expander("💡 Tips for Accurate Reading"):
            st.write("""
            - Cover camera completely with finger  
            - Keep finger steady  
            - Use good lighting or flash  
            - Avoid movement during measurement  
            """)

    if st.button("🔄 Measure Again"):
        st.rerun()

with tab3:

        st.header("🚶 Walking Progress Tracker")

        if "goal_steps" in st.session_state:
            step_tracker(st.session_state.goal_steps)
        else:
            st.info("Generate recommendation first.")
        

        if "history" not in st.session_state:
           st.session_state.history = []

        steps = st.session_state.get("steps_walked",0)

        if st.button("Save Today's Steps"):
           st.session_state.history.append(steps)

        st.subheader("📊 Walking History")
        
with tab4 : 
    st.title("🤖 Health Chat Assistant")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_input = st.chat_input("Ask something...")

    if user_input:
        st.session_state.messages.append(
            {"role": "user", "content": user_input}
        )

        if st.session_state.stress is not None:
            reply = chatbot_advice(
                st.session_state.stress,
                st.session_state.temp,
                st.session_state.humidity,
                st.session_state.duration,
                user_input
            )
        else:
            reply = "⚠ Please generate recommendation first."

        st.session_state.messages.append(
            {"role": "assistant", "content": reply}
        )

        st.rerun()

    if st.button("🧹 Clear Chat"):
         st.session_state.messages = []
         st.rerun()
