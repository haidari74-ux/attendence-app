import streamlit as st
import pandas as pd
from datetime import datetime
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import plotly.express as px

# --- إعدادات البريد الإلكتروني ---
EMAIL_SENDER = "haidari74@gmail.com" 
EMAIL_PASSWORD = "fmfmfm74"  
EMAIL_RECEIVER = "haidari74@gmail.com" 

# --- إعدادات الصفحة ---
st.set_page_config(page_title="نظام الحضور المتقدم", layout="wide", page_icon="📊")

# --- الهيكلة ---
levels_config = {
    "6ب": [f"6ب{i}" for i in range(1, 8)],
    "1ع": [f"1ع{i}" for i in range(1, 7)],
    "2ع": [f"2ع{i}" for i in range(1, 8)],
    "3ع": [f"3ع{i}" for i in range(1, 7)]
}

subjects = ["التربية الاسلامية", "اللغة العربية", "اللغة الانجليزية", "الرياضيات", "العلوم", "المواد الاجتماعية", "التربية الرياضية", "اللغة الفرنسية", "المجالات العملية"]
periods = ["الأولى", "الثانية", "الثالثة", "الرابعة", "الخامسة", "السادسة", "السابعة"]

# --- تحميل البيانات مع تنظيف الأعمدة ---
@st.cache_data
def load_students_data():
    file_path = "students.xlsx"
    if os.path.exists(file_path):
        try:
            df = pd.read_excel(file_path)
            # تنظيف أسماء الأعمدة من المسافات الزائدة (حل مشكلة KeyError)
            df.columns = [str(c).strip() for c in df.columns]
            return df
        except Exception as e:
            st.error(f"خطأ في قراءة ملف الإكسل: {e}")
    return None

students_df = load_students_data()

# --- القائمة الجانبية ---
with st.sidebar:
    st.header("⚙️ الإعدادات")
    teacher_name = st.text_input("👤 اسم المدرس")
    level_choice = st.selectbox("🏫 المرحلة", list(levels_config.keys()))
    class_choice = st.selectbox("🚪 الفرقة", levels_config[level_choice])
    subject_choice = st.selectbox("📚 المادة", subjects)
    period_choice = st.selectbox("🔔 الحصة", periods)
    send_email_toggle = st.checkbox("إرسال تقرير غياب", value=True)

# --- الواجهة الرئيسية ---
tab1, tab2 = st.tabs(["📝 تسجيل الحضور", "📊 الإحصائيات"])

with tab1:
    if students_df is not None:
        # تحديد أسماء الأعمدة المطلوبة
        col_name, col_level, col_class = 'اسم الطالب', 'الصف', 'الفرقة'
        
        # التأكد من وجود الأعمدة (حماية إضافية من KeyError)
        if all(c in students_df.columns for c in [col_name, col_level, col_class]):
            mask = (students_df[col_level].astype(str).str.strip() == level_choice) & \
                   (students_df[col_class].astype(str).str.strip() == class_choice)
            current_students = students_df[mask][col_name].tolist()

            if current_students:
                select_all = st.toggle("✅ تحديد الكل كحضور", value=True)
                attendance_results = []
                cols = st.columns(3)
                
                for idx, student in enumerate(current_students):
                    with cols[idx % 3]:
                        # مفتاح فريد لتجنب أخطاء الواجهة
                        key = f"{student}_{period_choice}_{subject_choice}"
                        is_p = st.checkbox(student, value=select_all, key=key)
                        attendance_results.append({
                            "التاريخ": datetime.now().strftime("%Y-%m-%d"),
                            "اسم الطالب": student, "الحالة": "حاضر" if is_p else "غائب",
                            "المرحلة": level_choice, "الفرقة": class_choice,
                            "المادة": subject_choice, "المدرس": teacher_name
                        })

                if st.button("💾 حفظ السجل", type="primary"):
                    if not teacher_name:
                        st.warning("يرجى إدخال اسم المدرس أولاً")
                    else:
                        out = "attendance_records.xlsx"
                        new_data = pd.DataFrame(attendance_results)
                        if os.path.exists(out):
                            final = pd.concat([pd.read_excel(out), new_data], ignore_index=True)
                        else:
                            final = new_data
                        final.to_excel(out, index=False)
                        
                        # إرسال التقرير
                        abs_list = [x['اسم الطالب'] for x in attendance_results if x['الحالة'] == 'غائب']
                        if send_email_toggle and abs_list:
                            try:
                                msg = MIMEMultipart()
                                msg['Subject'] = f"غياب {class_choice} - {subject_choice}"
                                body = f"المدرس: {teacher_name}\nالغائبون:\n" + "\n".join(abs_list)
                                msg.attach(MIMEText(body, 'plain', 'utf-8'))
                                with smtplib.SMTP('smtp.gmail.com', 587) as server:
                                    server.starttls()
                                    server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                                    server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
                                st.sidebar.success("📧 تم إرسال البريد")
                            except:
                                st.sidebar.error("❌ عطل في إرسال البريد")
                        st.success("✅ تم الحفظ بنجاح!")
            else:
                st.warning(f"لا يوجد طلاب في {class_choice} بملف الإكسل.")
        else:
            st.error(f"تأكد من وجود الأعمدة: '{col_name}', '{col_level}', '{col_class}' في ملف students.xlsx")
    else:
        st.error("يرجى رفع ملف 'students.xlsx' في نفس المجلد على GitHub.")

with tab2:
    if os.path.exists("attendance_records.xlsx"):
        df_stats = pd.read_excel("attendance_records.xlsx")
        # حساب نسبة الغياب لكل مرحلة
        stats = df_stats.groupby('المرحلة').apply(lambda x: (x['الحالة'] == 'غائب').sum() / len(x) * 100).reset_index(name='نسبة الغياب %')
        if not stats.empty:
            fig = px.bar(stats, x='المرحلة', y='نسبة الغياب %', title="معدل الغياب العام لكل مرحلة")
            st.plotly_chart(fig, use_container_width=True)