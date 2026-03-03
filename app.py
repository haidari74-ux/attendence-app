import streamlit as st
import pandas as pd
from datetime import datetime
import os
import io
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import plotly.express as px

# --- إعدادات البريد الإلكتروني (تم التحديث بناءً على طلبك) ---
EMAIL_SENDER = "haidari74@gmail.com" 
EMAIL_PASSWORD = "fmfmfm74"  
EMAIL_RECEIVER = "admin@school.com"  # يمكنك تغيير بريد الإدارة هنا

# --- إعدادات الصفحة ---
st.set_page_config(page_title="نظام الحضور المتقدم", layout="wide", page_icon="📊")

# --- الهيكلة الأساسية ---
levels_config = {
    "6ب": [f"6ب{i}" for i in range(1, 8)],
    "1ع": [f"1ع{i}" for i in range(1, 7)],
    "2ع": [f"2ع{i}" for i in range(1, 8)],
    "3ع": [f"3ع{i}" for i in range(1, 7)]
}

subjects = ["التربية الاسلامية", "اللغة العربية", "الرياضيات", "العلوم", "المواد الاجتماعية"]
periods = ["الأولى", "الثانية", "الثالثة", "الرابعة", "الخامسة", "السادسة", "السابعة"]
days = ["الأحد", "الأثنين", "الثلاثاء", "الأربعاء", "الخميس"]

# --- دالة إرسال البريد ---
def send_absentee_report(absentees, class_name, subject, teacher):
    if not absentees:
        return
    
    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = EMAIL_RECEIVER
    msg['Subject'] = f"تقرير غياب: {class_name} - {subject}"

    body = f"""
    تقرير غياب يوم {datetime.now().strftime('%Y-%m-%d')}
    المعلم: {teacher}
    الفصل: {class_name}
    المادة: {subject}
    
    أسماء الغائبين:
    {chr(10).join(['- ' + name for name in absentees])}
    """
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        st.sidebar.success("📧 تم إرسال تقرير الغياب بنجاح")
    except Exception as e:
        st.sidebar.error(f"❌ فشل إرسال البريد: {e}")

# --- تحميل البيانات ---
@st.cache_data
def load_students_data():
    file_path = "students.xlsx"
    if os.path.exists(file_path):
        return pd.read_excel(file_path)
    return None

students_df = load_students_data()

# --- القائمة الجانبية ---
with st.sidebar:
    st.header("⚙️ الإعدادات")
    teacher_name = st.text_input("👤 اسم المدرس")
    day_now = st.selectbox("📅 اليوم", days)
    level_choice = st.selectbox("🏫 المرحلة", list(levels_config.keys()))
    class_choice = st.selectbox("🚪 الفرقة", levels_config[level_choice])
    subject_choice = st.selectbox("📚 المادة", subjects)
    period_choice = st.selectbox("🔔 الحصة", periods)
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    send_email_toggle = st.checkbox("إرسال تقرير الغياب تلقائياً", value=True)

# --- الواجهة الرئيسية ---
tab1, tab2 = st.tabs(["📝 تسجيل الحضور", "📊 إحصائيات الغياب"])

with tab1:
    st.title("رصد حضور الطلاب")
    if students_df is not None:
        # تصفية الطلاب مع تنظيف المسافات
        students_df['الصف'] = students_df['الصف'].astype(str).str.strip()
        students_df['الفرقة'] = students_df['الفرقة'].astype(str).str.strip()
        
        mask = (students_df['الصف'] == level_choice) & (students_df['الفرقة'] == class_choice)
        current_students = students_df[mask]['اسم الطالب'].tolist()

        if current_students:
            select_all = st.toggle("✅ تحديد الكل كحضور", value=True)
            attendance_results = []
            
            cols = st.columns(3)
            for idx, student in enumerate(current_students):
                with cols[idx % 3]:
                    # استخدام مفتاح فريد لتجنب أخطاء Streamlit
                    key = f"{student}_{period_choice}_{subject_choice}"
                    is_present = st.checkbox(student, value=select_all, key=key)
                    attendance_results.append({
                        "التاريخ": date_str, "اسم الطالب": student,
                        "الحالة": "حاضر" if is_present else "غائب",
                        "المرحلة": level_choice, "الفرقة": class_choice,
                        "المادة": subject_choice, "المدرس": teacher_name
                    })

            if st.button("💾 حفظ السجل", type="primary"):
                if not teacher_name:
                    st.error("يرجى كتابة اسم المدرس")
                else:
                    new_data = pd.DataFrame(attendance_results)
                    output_file = "attendance_records.xlsx"
                    
                    if os.path.exists(output_file):
                        final_df = pd.concat([pd.read_excel(output_file), new_data], ignore_index=True)
                    else:
                        final_df = new_data
                    final_df.to_excel(output_file, index=False)
                    
                    # إرسال التقرير للغائبين
                    absentees = [x['اسم الطالب'] for x in attendance_results if x['الحالة'] == 'غائب']
                    if send_email_toggle and absentees:
                        send_absentee_report(absentees, class_choice, subject_choice, teacher_name)
                    
                    st.success("✅ تم الحفظ وتحديث السجلات")
                    st.balloons()
        else:
            st.warning("لا يوجد طلاب مسجلين في هذه الفرقة")

with tab2:
    st.title("تحليل نسب الغياب")
    if os.path.exists("attendance_records.xlsx"):
        df_stats = pd.read_excel("attendance_records.xlsx")
        
        # تجميع البيانات لحساب النسب لكل صف (مرحلة)
        total_by_level = df_stats.groupby('المرحلة').size().reset_index(name='الإجمالي')
        absent_by_level = df_stats[df_stats['الحالة'] == 'غائب'].groupby('المرحلة').size().reset_index(name='الغياب')
        
        stats_df = pd.merge(total_by_level, absent_by_level, on='المرحلة', how='left').fillna(0)
        stats_df['نسبة الغياب %'] = (stats_df['الغياب'] / stats_df['الإجمالي']) * 100

        # رسم بياني تفاعلي
        fig = px.bar(stats_df, x='المرحلة', y='نسبة الغياب %', 
                     title="معدل الغياب لكل مرحلة دراسية",
                     color='المرحلة', text_auto='.1f',
                     color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig, use_container_width=True)
        
        st.table(stats_df)
    else:
        st.info("سجل الحضور فارغ. ابدأ برصد الحضور لعرض الإحصائيات.")