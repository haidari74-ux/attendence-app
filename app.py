import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- إعدادات الصفحة ---
st.set_page_config(page_title="نظام الحضور المدرسي", layout="centered")

st.markdown("""
    <style>
    .stCheckbox { background-color: #f9f9f9; padding: 12px; border-radius: 10px; border: 1px solid #ddd; margin-bottom: 5px; }
    .stButton>button { width: 100%; border-radius: 25px; height: 3.5em; background-color: #28a745; color: white; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.title("📋 سجل الحضور والغياب")

# --- أولاً: الهيكلة المحدثة بالأرقام الإنجليزية ---
levels_config = {
    "6ب": [f"6ب{i}" for i in range(1, 8)],
    "1ع": [f"1ع{i}" for i in range(1, 7)],
    "2ع": [f"2ع{i}" for i in range(1, 8)],
    "3ع": [f"3ع{i}" for i in range(1, 7)]
}

subjects = ["التربية الاسلامية", "اللغة العربية", "اللغة الانجليزية", "الرياضيات", "العلوم", "المواد الاجتماعية"]
periods = ["الأولى", "الثانية", "الثالثة", "الرابعة", "الخامسة", "السادسة", "السابعة"]
days = ["الأحد", "الأثنين", "الثلاثاء", "الأربعاء", "الخميس"]

# --- ثانياً: تحميل البيانات من الإكسل ---
@st.cache_data
def load_students_data():
    file_path = "students.xlsx"
    if os.path.exists(file_path):
        df = pd.read_excel(file_path)
        df.columns = ['اسم الطالب', 'الصف', 'الفرقة'] + list(df.columns[3:])
        # تنظيف البيانات وتحويلها لنصوص لضمان المطابقة
        df['الصف'] = df['الصف'].astype(str).str.strip()
        df['الفرقة'] = df['الفرقة'].astype(str).str.strip()
        return df
    else:
        st.error(f"⚠️ الملف '{file_path}' غير موجود!")
        return None

students_df = load_students_data()

# --- ثالثاً: واجهة الإعدادات ---
with st.sidebar:
    st.header("⚙️ الإعدادات")
    teacher_name = st.text_input("👤 اسم المدرس")
    day_now = st.selectbox("📅 اليوم", days)
    level_choice = st.selectbox("🏫 المرحلة", list(levels_config.keys()))
    class_choice = st.selectbox("🚪 الفرقة", levels_config[level_choice])
    subject_choice = st.selectbox("📚 المادة", subjects)
    period_choice = st.selectbox("🔔 الحصة", periods)
    date_str = datetime.now().strftime("%Y-%m-%d")

# --- رابعاً: عرض قائمة الطلاب ---
st.subheader(f"📍 كشف: {class_choice} | {subject_choice}")

if students_df is not None:
    # التصفية بناءً على الأرقام الإنجليزية (6ب، 1ع، إلخ)
    current_students = students_df[
        (students_df['الصف'] == level_choice) & 
        (students_df['الفرقة'] == class_choice)
    ]['اسم الطالب'].tolist()
    
    if current_students:
        select_all = st.checkbox("✅ تحديد الكل كحضور")
        
        attendance_results = []
        for student in current_students:
            is_present = st.checkbox(student, value=select_all, key=f"{class_choice}_{student}")
            attendance_results.append({
                "اسم الطالب": student,
                "الحالة": "حاضر" if is_present else "غائب"
            })
            
        # --- خامساً: الحفظ ---
        if st.button("💾 حفظ السجل"):
            if not teacher_name:
                st.warning("يرجى كتابة اسم المدرس.")
            else:
                final_df = pd.DataFrame(attendance_results)
                final_df['المدرس'] = teacher_name
                final_df['المرحلة'] = level_choice
                final_df['الفرقة'] = class_choice
                final_df['المادة'] = subject_choice
                final_df['الحصة'] = period_choice
                final_df['التاريخ'] = date_str
                
                output_file = "attendance_records.csv"
                file_exists = os.path.isfile(output_file)
                final_df.to_csv(output_file, mode='a', index=False, header=not file_exists, encoding='utf-8-sig')
                
                st.success(f"تم تسجيل حضور {class_choice} بنجاح!")
                st.balloons()
    else:
        st.info(f"لم يتم العثور على طلاب في {class_choice}. تأكد أن البيانات في الإكسل مكتوبة كـ {class_choice}.")

# عرض السجلات السابقة
if st.checkbox("👁️ عرض سجلات اليوم"):
    if os.path.exists("attendance_records.csv"):
        st.table(pd.read_csv("attendance_records.csv").tail(15))

