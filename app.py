import streamlit as st
import pandas as pd
from datetime import datetime
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import plotly.express as px

# --- بياناتك الخاصة ---
EMAIL_SENDER = "haidari74@gmail.com" 
EMAIL_PASSWORD = "fmfmfm74"  
EMAIL_RECEIVER = "haidari74@gmail.com" 

# --- إعدادات الصفحة ---
st.set_page_config(page_title="نظام الحضور المطور", layout="wide")

# --- هيكلة الصفوف ---
levels_config = {
    "6ب": [f"6ب{i}" for i in range(1, 8)],
    "1ع": [f"1ع{i}" for i in range(1, 7)],
    "2ع": [f"2ع{i}" for i in range(1, 8)],
    "3ع": [f"3ع{i}" for i in range(1, 7)]
}

subjects = ["التربية الاسلامية", "اللغة العربية", "اللغة الانجليزية", "الرياضيات", "العلوم", "المواد الاجتماعية", "التربية الرياضية", "اللغة الفرنسية", "المجالات العملية"]
periods = ["الأولى", "الثانية", "الثالثة", "الرابعة", "الخامسة", "السادسة", "السابعة"]

# --- دالة تحميل البيانات ومعالجة الأعمدة بذكاء ---
@st.cache_data
def load_students_data():
    file_path = "students.xlsx"
    if not os.path.exists(file_path):
        st.error(f"⚠️ الملف '{file_path}' غير موجود في المستودع.")
        return None
    try:
        df = pd.read_excel(file_path)
        # تنظيف شامل لأسماء الأعمدة من أي مسافات
        df.columns = [str(c).strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"❌ خطأ في قراءة ملف الإكسل: {e}")
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
    send_email_toggle = st.checkbox("إرسال تقرير غياب تلقائي", value=True)

# --- التبويبات الرئيسية ---
tab1, tab2 = st.tabs(["📝 تسجيل الحضور", "📊 إحصائيات الغياب"])

with tab1:
    if students_df is not None:
        # حل مشكلة KeyError: البحث عن الأعمدة بالمعنى وليس بالاسم الجامد
        col_student = next((c for c in students_df.columns if 'اسم' in c), None)
        col_level = next((c for c in students_df.columns if 'صف' in c or 'مرحلة' in c), None)
        col_class = next((c for c in students_df.columns if 'فرقة' in c or 'فصل' in c), None)
        
        if col_student and col_level and col_class:
            # تصفية الطلاب بناءً على الاختيارات
            mask = (students_df[col_level].astype(str).str.strip() == level_choice) & \
                   (students_df[col_class].astype(str).str.strip() == class_choice)
            current_students = students_df[mask][col_student].tolist()

            if current_students:
                select_all = st.toggle("✅ تحديد الكل كحضور", value=True)
                attendance_results = []
                
                # عرض الأسماء في 3 أعمدة لتوفير المساحة
                cols = st.columns(3)
                for idx, student in enumerate(current_students):
                    with cols[idx % 3]:
                        is_p = st.checkbox(student, value=select_all, key=f"chk_{idx}_{period_choice}")
                        attendance_results.append({
                            "التاريخ": datetime.now().strftime("%Y-%m-%d"),
                            "اسم الطالب": student,
                            "الحالة": "حاضر" if is_p else "غائب",
                            "المرحلة": level_choice,
                            "الفرقة": class_choice,
                            "المادة": subject_choice,
                            "المدرس": teacher_name
                        })

                if st.button("💾 حفظ البيانات وإرسال الإيميل", type="primary"):
                    if not teacher_name:
                        st.warning("⚠️ يرجى إدخال اسم المدرس أولاً")
                    else:
                        # حفظ في ملف السجلات
                        out_file = "attendance_records.xlsx"
                        new_df = pd.DataFrame(attendance_results)
                        if os.path.exists(out_file):
                            final_df = pd.concat([pd.read_excel(out_file), new_df], ignore_index=True)
                        else:
                            final_df = new_df
                        final_df.to_excel(out_file, index=False)
                        
                        # إرسال التقرير للغائبين فقط
                        absentees = [x['اسم الطالب'] for x in attendance_results if x['الحالة'] == 'غائب']
                        if send_email_toggle and absentees:
                            try:
                                msg = MIMEMultipart()
                                msg['Subject'] = f"تقرير غياب: {class_choice} - {subject_choice}"
                                body = f"المدرس: {teacher_name}\nالتاريخ: {datetime.now().strftime('%Y-%m-%d')}\n\nالغائبون:\n" + "\n".join(["- " + name for name in absentees])
                                msg.attach(MIMEText(body, 'plain', 'utf-8'))
                                with smtplib.SMTP('smtp.gmail.com', 587) as server:
                                    server.starttls()
                                    server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                                    server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
                                st.sidebar.success("📧 تم إرسال البريد بنجاح")
                            except:
                                st.sidebar.error("❌ فشل إرسال البريد")
                        
                        st.success("✅ تم حفظ التحضير بنجاح")
            else:
                st.warning(f"لم يتم العثور على طلاب في {class_choice}. تأكد من البيانات في ملف الإكسل.")
        else:
            st.error(f"❌ لم يتم التعرف على أعمدة الملف. تأكد أن الملف يحتوي على: 'اسم الطالب' و 'الصف' و 'الفرقة'.")

with tab2:
    if os.path.exists("attendance_records.xlsx"):
        df_stats = pd.read_excel("attendance_records.xlsx")
        # حساب النسبة المئوية للغياب لكل مرحلة
        stats = df_stats.groupby('المرحلة').apply(lambda x: (x['الحالة'] == 'غائب').sum() / len(x) * 100).reset_index(name='نسبة الغياب %')
        
        if not stats.empty:
            fig = px.bar(stats, x='المرحلة', y='نسبة الغياب %', title="معدل الغياب العام حسب المرحلة", color='المرحلة')
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(stats)
        else:
            st.info("لا توجد بيانات كافية لعرض الإحصائيات بعد.")