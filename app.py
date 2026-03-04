import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- إعدادات الصفحة ---
st.set_page_config(page_title="نظام الحضور المدرسي الذكي", layout="wide", page_icon="📝")

# تصميم CSS مخصص لبهجة الواجهة
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stCheckbox { background-color: white; padding: 10px; border-radius: 8px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); margin-bottom: 5px; }
    .stButton>button { border-radius: 12px; height: 3em; background-color: #4CAF50; color: white; transition: 0.3s; }
    .stButton>button:hover { background-color: #45a049; border: 1px solid white; }
    div[data-testid="stExpander"] { background-color: white; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- الهيكلة ---
levels_config = {
    "6ب": [f"6ب{i}" for i in range(1, 8)],
    "1ع": [f"1ع{i}" for i in range(1, 7)],
    "2ع": [f"2ع{i}" for i in range(1, 8)],
    "3ع": [f"3ع{i}" for i in range(1, 7)]
}
subjects = ["التربية الاسلامية", "اللغة العربية", "اللغة الانجليزية", "الرياضيات", "العلوم", "المواد الاجتماعية"]
periods = ["الأولى", "الثانية", "الثالثة", "الرابعة", "الخامسة", "السادسة", "السابعة"]

# --- دالة تحميل البيانات ---
@st.cache_data
def load_students_data():
    file_path = "students.xlsx"
    if os.path.exists(file_path):
        try:
            df = pd.read_excel(file_path)
            # التأكد من تنظيف أسماء الأعمدة من المسافات
            df.columns = [col.strip() for col in df.columns]
            # تحويل الأعمدة لنصوص وتنظيفها
            for col in ['الصف', 'الفرقة']:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip()
            return df
        except Exception as e:
            st.error(f"خطأ في قراءة الملف: {e}")
            return None
    else:
        st.warning("⚠️ ملف 'students.xlsx' غير موجود. يرجى رفعه في مجلد المشروع.")
        return None

students_df = load_students_data()

# --- القائمة الجانبية (الإعدادات) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3449/3449692.png", width=100)
    st.header("⚙️ إعدادات الحصة")
    teacher_name = st.text_input("👤 اسم المدرس", placeholder="أدخل اسمك هنا...")
    
    col1, col2 = st.columns(2)
    with col1:
        level_choice = st.selectbox("🏫 المرحلة", list(levels_config.keys()))
    with col2:
        class_choice = st.selectbox("🚪 الفرقة", levels_config[level_choice])
        
    subject_choice = st.selectbox("📚 المادة", subjects)
    period_choice = st.selectbox("🔔 الحصة", periods)
    date_now = datetime.now().strftime("%Y-%m-%d")

# --- الواجهة الرئيسية ---
st.title("📋 سجل الحضور والغياب الرقمي")
st.info(f"📅 التاريخ: {date_now} | 🕒 الحصة: {period_choice} | 📍 الصف: {class_choice}")

if students_df is not None:
    # تصفية الطلاب
    mask = (students_df['الصف'] == level_choice) & (students_df['الفرقة'] == class_choice)
    current_students = students_df[mask]['اسم الطالب'].tolist()

    if current_students:
        # خيار تحديد الكل
        col_all, col_empty = st.columns([1, 3])
        with col_all:
            select_all = st.toggle("✅ تحديد الكل كحضور", value=True)

        st.divider()
        
        # عرض الطلاب في أعمدة (لتقليل طول الصفحة)
        cols = st.columns(2)
        attendance_dict = {}
        
        for idx, student in enumerate(current_students):
            with cols[idx % 2]:
                # استخدام مفتاح فريد لكل طالب يتضمن التاريخ والحصة لمنع التداخل
                key = f"{date_now}_{period_choice}_{student}"
                is_present = st.checkbox(student, value=select_all, key=key)
                attendance_dict[student] = "حاضر" if is_present else "غائب"

        st.divider()

        # زر الحفظ
        if st.button("💾 حفظ وإرسال السجل"):
            if not teacher_name:
                st.error("❗ يرجى إدخال اسم المدرس أولاً في القائمة الجانبية.")
            else:
                # تجهيز البيانات للحفظ
                records = []
                for name, status in attendance_dict.items():
                    records.append({
                        "التاريخ": date_now,
                        "المدرس": teacher_name,
                        "المرحلة": level_choice,
                        "الفرقة": class_choice,
                        "الحصة": period_choice,
                        "المادة": subject_choice,
                        "اسم الطالب": name,
                        "الحالة": status
                    })
                
                new_data = pd.DataFrame(records)
                output_file = "attendance_records.csv"
                
                # حفظ الملف مع دعم اللغة العربية
                if os.path.exists(output_file):
                    new_data.to_csv(output_file, mode='a', index=False, header=False, encoding='utf-8-sig')
                else:
                    new_data.to_csv(output_file, index=False, encoding='utf-8-sig')
                
                st.success(f"✅ تم حفظ التحضير لـ {len(current_students)} طالب بنجاح!")
                st.balloons()
    else:
        st.warning(f"🔍 لم يتم العثور على طلاب مسجلين في {class_choice}. تأكد من مطابقة البيانات في ملف الإكسل.")

# --- قسم استعراض السجلات ---
with st.expander("👁️ استعراض سجلات الحضور السابقة"):
    if os.path.exists("attendance_records.csv"):
        view_df = pd.read_csv("attendance_records.csv")
        st.dataframe(view_df.tail(20), use_container_width=True)
        
        # زر لتحميل الملف كاملاً
        csv = view_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 تحميل السجل الكامل (CSV)", data=csv, file_name=f"attendance_{date_now}.csv", mime="text/csv")
    else:
        st.info("لا توجد سجلات محفوظة حتى الآن.")