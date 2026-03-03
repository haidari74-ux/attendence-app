import streamlit as st
import pandas as pd
from datetime import datetime
import os
import io
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import plotly.express as px

# --- إعدادات البريد الإلكتروني ---
EMAIL_SENDER = "haidari74@gmail.com" 
EMAIL_PASSWORD = "fmfmfm74"  
EMAIL_RECEIVER = "admin@school.com" 

# --- إعدادات الصفحة ---
st.set_page_config(page_title="نظام الحضور المتقدم", layout="wide", page_icon="📊")

# --- الهيكلة ---
levels_config = {
    "6ب": [f"6ب{i}" for i in range(1, 8)],
    "1ع": [f"1ع{i}" for i in range(1, 7)],
    "2ع": [f"2ع{i}" for i in range(1, 8)],
    "3ع": [f"3ع{i}" for i in range(1, 7)]
}

# تم تحديث القائمة بالمواد الجديدة كما طلبت
subjects = ["التربية الاسلامية", "اللغة العربية", "اللغة الانجليزية", "الرياضيات", "العلوم", "المواد الاجتماعية", "التربية الرياضية", "اللغة الفرنسية", "المجالات العملية"]
periods = ["الأولى", "الثانية", "الثالثة", "الرابعة", "الخامسة", "السادسة", "السابعة"]
days = ["الأحد", "الأثنين", "الثلاثاء", "الأربعاء", "الخميس"]

# --- دالة إرسال البريد ---
def send_absentee_report(absentees, class_name, subject, teacher):
    if not absentees: return
    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = f"تقرير غياب: {class_name} - {subject}"
    body = f"تقرير غياب يوم {datetime.now().strftime('%Y-%m-%d')}\nالمعلم: {teacher}\nالفصل: {class_name}\nالمادة: {subject}\n\nالغائبون:\n" + "\n".join(["- " + name for name in absentees])
    msg.attach(MIMEText(body, 'plain', 'utf-8'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587); server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg); server.quit()
        st.sidebar.success("📧 تم إرسال البريد")
    except: st.sidebar.error("❌ فشل إرسال البريد")

# --- تحميل البيانات ---
@st.cache_data
def load_students_data():
    file_path = "students.xlsx"
    if os.path.exists(file_path):
        df = pd.read_excel(file_path)
        # تنظيف أسماء الأعمدة من أي مسافات زائدة قد تسبب الخطأ
        df.columns = [c.strip() for c in df.columns]
        return df
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
        # حل مشكلة KeyError: التأكد من وجود الأعمدة قبل التصفية
        required_cols = ['الصف', 'الفرقة', 'اسم الطالب']
        if all(col in students_df.columns for col in required_cols):
            mask = (students_df['الصف'].astype(str).str.strip() == level_choice) & \
                   (students_df['الفرقة'].astype(str).str.strip() == class_choice)
            current_students = students_df[mask]['اسم الطالب'].tolist()

            if current_students:
                select_all = st.toggle("✅ تحديد الكل كحضور", value=True)
                attendance_results = []
                cols = st.columns(3)
                for idx, student in enumerate(current_students):
                    with cols[idx % 3]:
                        is_p = st.checkbox(student, value=select_all, key=f"{student}_{period_choice}")
                        attendance_results.append({
                            "التاريخ": datetime.now().strftime("%Y-%m-%d"),
                            "اسم الطالب": student, "الحالة": "حاضر" if is_p else "غائب",
                            "المرحلة": level_choice, "الفرقة": class_choice,
                            "المادة": subject_choice, "المدرس": teacher_name
                        })

                if st.button("💾 حفظ السجل", type="primary"):
                    if not teacher_name: st.warning("اكتب اسمك أولاً")
                    else:
                        out = "attendance_records.xlsx"
                        final = pd.concat([pd.read_excel(out) if os.path.exists(out) else pd.DataFrame(), pd.DataFrame(attendance_results)], ignore_index=True)
                        final.to_excel(out, index=False)
                        abs = [x['اسم الطالب'] for x in attendance_results if x['الحالة'] == 'غائب']
                        if send_email_toggle: send_absentee_report(abs, class_choice, subject_choice, teacher_name)
                        st.success("تم الحفظ!")
            else:
                st.warning("لم يتم العثور على طلاب لهذه الفرقة.")
        else:
            st.error(f"❌ خطأ في ملف الإكسل! يجب أن يحتوي على الأعمدة: {required_cols}. الأعمدة الحالية هي: {list(students_df.columns)}")
    else:
        st.error("ملف students.xlsx غير موجود.")

with tab2:
    if os.path.exists("attendance_records.xlsx"):
        df_stats = pd.read_excel("attendance_records.xlsx")
        stats = df_stats.groupby('المرحلة').apply(lambda x: (x['الحالة'] == 'غائب').sum() / len(x) * 100).reset_index(name='نسبة الغياب %')
        fig = px.bar(stats, x='المرحلة', y='نسبة الغياب %', title="نسبة الغياب لكل مرحلة")
        st.plotly_chart(fig, use_container_width=True)