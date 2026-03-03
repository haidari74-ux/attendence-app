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
EMAIL_RECEIVER = "haidari74@gmail.com" # تم توحيده لضمان وصول التقرير لك

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

# --- تحميل البيانات مع معالجة ذكية للأعمدة ---
@st.cache_data
def load_students_data():
    file_path = "students.xlsx"
    if os.path.exists(file_path):
        try:
            df = pd.read_excel(file_path)
            # تنظيف المسافات من أسماء الأعمدة
            df.columns = [str(c).strip() for c in df.columns]
            return df
        except Exception as e:
            st.error(f"خطأ في قراءة ملف الطلاب: {e}")
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
    send_email_toggle = st.checkbox("إرسال تقرير بالبريد", value=True)

# --- الواجهة الرئيسية ---
tab1, tab2 = st.tabs(["📝 تسجيل الحضور", "📊 الإحصائيات"])

with tab1:
    if students_df is not None:
        # التحقق من أسماء الأعمدة (حل مشكلة KeyError)
        col_name = 'اسم الطالب'
        level_col = 'الصف'
        class_col = 'الفرقة'
        
        if all(c in students_df.columns for c in [col_name, level_col, class_col]):
            mask = (students_df[level_col].astype(str).str.strip() == level_choice) & \
                   (students_df[class_col].astype(str).str.strip() == class_choice)
            current_students = students_df[mask][col_name].tolist()

            if current_students:
                select_all = st.toggle("✅ تحديد الكل كحضور", value=True)
                attendance_results = []
                cols = st.columns(3)
                
                for idx, student in enumerate(current_students):
                    with cols[idx % 3]:
                        is_p = st.checkbox(student, value=select_all, key=f"{student}_{period_choice}")
                        attendance_results.append({
                            "التاريخ": datetime.now().strftime("%Y-%m-%d"),
                            "اسم الطالب": student, 
                            "الحالة": "حاضر" if is_p else "غائب",
                            "المرحلة": level_choice, 
                            "الفرقة": class_choice,
                            "المادة": subject_choice, 
                            "المدرس": teacher_name
                        })

                if st.button("💾 حفظ السجل", type="primary"):
                    if not teacher_name:
                        st.warning("الرجاء إدخال اسم المدرس أولاً")
                    else:
                        out_file = "attendance_records.xlsx"
                        new_df = pd.DataFrame(attendance_results)
                        
                        if os.path.exists(out_file):
                            existing_df = pd.read_excel(out_file)
                            final_df = pd.concat([existing_df, new_df], ignore_index=True)
                        else:
                            final_df = new_df
                        
                        final_df.to_excel(out_file, index=False)
                        
                        # إرسال البريد
                        absentees = [x['اسم الطالب'] for x in attendance_results if x['الحالة'] == 'غائب']
                        if send_email_toggle and absentees:
                            # دالة الإرسال (مبسطة)
                            try:
                                msg = MIMEMultipart()
                                msg['Subject'] = f"غياب {class_choice} - {subject_choice}"
                                body = f"المدرس: {teacher_name}\nالغائبون:\n" + "\n".join(absentees)
                                msg.attach(MIMEText(body, 'plain', 'utf-8'))
                                with smtplib.SMTP('smtp.gmail.com', 587) as server:
                                    server.starttls()
                                    server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                                    server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
                                st.sidebar.success("📧 تم إرسال التقرير!")
                            except:
                                st.sidebar.error("❌ عطل في إرسال البريد")
                        
                        st.success("✅ تم الحفظ بنجاح!")
            else:
                st.warning(f"لا يوجد طلاب في {class_choice} داخل ملف الإكسل.")
        else:
            st.error(f"الملف لا يحتوي على الأعمدة المطلوبة: {level_col}, {class_col}, {col_name}")
    else:
        st.error("يرجى التأكد من رفع ملف 'students.xlsx' في المجلد الرئيسي.")

with tab2:
    if os.path.exists("attendance_records.xlsx"):
        df_stats = pd.read_excel("attendance_records.xlsx")
        # حساب النسبة لكل صف
        stats = df_stats.groupby('المرحلة').apply(lambda x: (x['الحالة'] == 'غائب').sum() / len(x) * 100).reset_index(name='نسبة الغياب %')
        
        if not stats.empty:
            fig = px.bar(stats, x='المرحلة', y='نسبة الغياب %', title="معدل الغياب العام حسب المرحلة")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("لا توجد بيانات غياب كافية للرسم البياني.")