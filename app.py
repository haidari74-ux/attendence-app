import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- إعدادات الصفحة ---
st.set_page_config(page_title="نظام الحضور - إصدار إكسل", layout="centered")

# --- الهيكلة ---
levels_config = {
    "6ب": [f"6ب{i}" for i in range(1, 8)],
    "1ع": [f"1ع{i}" for i in range(1, 7)],
    "2ع": [f"2ع{i}" for i in range(1, 8)],
    "3ع": [f"3ع{i}" for i in range(1, 7)]
}

subjects = ["التربية الاسلامية", "اللغة العربية", "اللغة الانجليزية", "الرياضيات", "العلوم", "المواد الاجتماعية","التربية الرياضية","اللغة الفرنسية","المجالات العملية"]
periods = ["الأولى", "الثانية", "الثالثة", "الرابعة", "الخامسة", "السادسة", "السابعة"]
days = ["الأحد", "الأثنين", "الثلاثاء", "الأربعاء", "الخميس"]

# --- تحميل بيانات الطلاب (المصدر) ---
@st.cache_data
def load_students_data():
    file_path = "students.xlsx"
    if os.path.exists(file_path):
        return pd.read_excel(file_path)
    else:
        st.error(f"⚠️ ملف '{file_path}' غير موجود!")
        return None

students_df = load_students_data()

# --- واجهة الإعدادات الجانبية ---
with st.sidebar:
    st.header("⚙️ الإعدادات")
    teacher_name = st.text_input("👤 اسم المدرس")
    day_now = st.selectbox("📅 اليوم", days)
    level_choice = st.selectbox("🏫 المرحلة", list(levels_config.keys()))
    class_choice = st.selectbox("🚪 الفرقة", levels_config[level_choice])
    subject_choice = st.selectbox("📚 المادة", subjects)
    period_choice = st.selectbox("🔔 الحصة", periods)
    date_str = datetime.now().strftime("%Y-%m-%d")

# --- عرض قائمة الطلاب وتسجيل الحضور ---
st.title("📋 سجل الحضور والغياب (Excel)")

if students_df is not None:
    # تصفية الطلاب
    mask = (students_df['الصف'].astype(str).str.strip() == level_choice) & \
           (students_df['الفرقة'].astype(str).str.strip() == class_choice)
    current_students = students_df[mask]['اسم الطالب'].tolist()

    if current_students:
        select_all = st.checkbox("✅ تحديد الكل كحضور")
        attendance_results = []

        for student in current_students:
            is_present = st.checkbox(student, value=select_all, key=f"{class_choice}_{student}")
            attendance_results.append({
                "التاريخ": date_str,
                "اليوم": day_now,
                "اسم الطالب": student,
                "الحالة": "حاضر" if is_present else "غائب",
                "المرحلة": level_choice,
                "الفرقة": class_choice,
                "المادة": subject_choice,
                "الحصة": period_choice,
                "المدرس": teacher_name
            })

        # --- منطق الحفظ في ملف إكسل ---
        if st.button("💾 حفظ في ملف Excel"):
            if not teacher_name:
                st.warning("يرجى كتابة اسم المدرس.")
            else:
                new_data = pd.DataFrame(attendance_results)
                output_file = "attendance_records.xlsx"

                # التحقق إذا كان الملف موجوداً مسبقاً لدمج البيانات
                if os.path.exists(output_file):
                    existing_df = pd.read_excel(output_file)
                    final_df = pd.concat([existing_df, new_data], ignore_index=True)
                else:
                    final_df = new_data

                # حفظ الملف بصيغة إكسل
                final_df.to_excel(output_file, index=False)
                
                st.success(f"✅ تم الحفظ في ملف {output_file} بنجاح!")
                st.balloons()
    else:
        st.info("لم يتم العثور على طلاب لهذه الفرقة.")

# --- عرض وتحميل السجل الحالي ---
st.divider()
if st.checkbox("👁️ عرض السجلات المحفوظة"):
    if os.path.exists("attendance_records.xlsx"):
        df_view = pd.read_excel("attendance_records.xlsx")
        st.dataframe(df_view.tail(20))
        
        # زر لتحميل الملف للمستخدم
        with open("attendance_records.xlsx", "rb") as f:
            st.download_button(
                label="📥 تحميل ملف الإكسل كاملاً",
                data=f,
                file_name="تقرير_الحضور.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )