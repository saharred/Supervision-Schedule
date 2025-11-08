"""
Complete Exam Supervision Schedule Generator with Sections Support
- Level 1 (Grade 1-2): Teachers only
- Level 2 (Grade 3-4): Teachers + Teaching Assistants (Sections)
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import re
from collections import defaultdict
import random

# Import custom modules
from logic_v2 import get_day_name_arabic
from export_word import export_to_word
from export_pdf_v2 import export_to_pdf_v2

# Page configuration
st.set_page_config(
    page_title="جدول المراقبة للاختبارات - نظام كامل",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Tajawal', 'Tahoma', sans-serif;
        direction: rtl;
        text-align: right;
    }
    
    .stButton>button {
        width: 100%;
        background-color: #8B0000;
        color: white;
        font-weight: bold;
        border-radius: 5px;
        padding: 10px;
        font-size: 16px;
    }
    
    .stButton>button:hover {
        background-color: #A52A2A;
    }
    
    h1, h2, h3 {
        color: #8B0000;
    }
    
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
        color: #155724;
    }
    
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)

# Helper functions
def parse_date_arabic(date_str):
    """Parse Arabic date format"""
    if pd.isna(date_str):
        return None
    
    match = re.search(r'(\d{4})/(\d{1,2})/(\d{1,2})', str(date_str))
    if match:
        year, month, day = match.groups()
        return datetime(int(year), int(month), int(day))
    return None

def parse_exam_schedule(file):
    """Parse exam schedule from Excel file"""
    df = pd.read_excel(file)
    
    exams = []
    
    for _, row in df.iterrows():
        date = parse_date_arabic(row['اليوم والتاريخ'])
        if not date:
            continue
        
        level = str(row['المستوى']).strip()
        
        # Parse session 2
        if pd.notna(row['الحصة الثانية']) and str(row['الحصة الثانية']).strip() != '':
            subject = str(row['الحصة الثانية']).strip()
            if 'يوجد' not in subject:
                exams.append({
                    'date': date,
                    'session': 'الحصة الثانية',
                    'start_time': '08:00',
                    'end_time': '10:00',
                    'subject': subject,
                    'level': level,
                    'grade': level,
                    'section': '',
                    'supervisor1': '',
                    'supervisor2': ''
                })
        
        # Parse sessions 3&4
        if pd.notna(row['الحصة الثالثة والرابعة']) and str(row['الحصة الثالثة والرابعة']).strip() != '':
            subject = str(row['الحصة الثالثة والرابعة']).strip()
            if 'يوجد' not in subject:
                exams.append({
                    'date': date,
                    'session': 'الحصة الثالثة والرابعة',
                    'start_time': '10:30',
                    'end_time': '12:30',
                    'subject': subject,
                    'level': level,
                    'grade': level,
                    'section': '',
                    'supervisor1': '',
                    'supervisor2': ''
                })
    
    return pd.DataFrame(exams)

def assign_supervisors_smart(exams_df, teachers_df, sections_df):
    """
    Assign supervisors intelligently:
    - Level 1 (أول): Teachers only
    - Level 2 (الثاني): Teachers + Sections (Teaching Assistants)
    """
    
    # Prepare teachers list
    teachers_list = teachers_df['teacher_name'].tolist()
    teacher_specialty = dict(zip(teachers_df['teacher_name'], teachers_df['specialty']))
    
    # Prepare sections list
    sections_list = sections_df['الصف'].tolist() if sections_df is not None else []
    
    # Track assignments
    teacher_daily_count = defaultdict(lambda: defaultdict(int))
    teacher_total_count = defaultdict(int)
    section_daily_count = defaultdict(lambda: defaultdict(int))
    section_total_count = defaultdict(int)
    
    # Assign supervisors
    for idx, exam in exams_df.iterrows():
        date_str = exam['date'].strftime('%Y-%m-%d')
        subject = exam['subject']
        level = exam['level']
        
        # Determine if this is level 1 or level 2
        is_level_one = 'أول' in level or 'الأول' in level or 'ثاني' in level or 'الثاني' in level
        
        # Assign supervisor 1 (always a teacher)
        available_teachers = [
            t for t in teachers_list
            if teacher_daily_count[t][date_str] < 3
        ]
        
        # Prefer different specialty
        different_specialty = [
            t for t in available_teachers
            if teacher_specialty.get(t, '').strip() != subject.strip()
        ]
        
        if different_specialty:
            available_teachers = different_specialty
        
        # Sort by total count (load balancing)
        available_teachers.sort(key=lambda t: teacher_total_count[t])
        
        if available_teachers:
            supervisor1 = available_teachers[0]
            exams_df.at[idx, 'supervisor1'] = supervisor1
            teacher_daily_count[supervisor1][date_str] += 1
            teacher_total_count[supervisor1] += 1
        
        # Assign supervisor 2
        if is_level_one:
            # Level 1: Another teacher
            available_teachers2 = [
                t for t in teachers_list
                if t != supervisor1 and teacher_daily_count[t][date_str] < 3
            ]
            
            # Prefer different specialty
            different_specialty2 = [
                t for t in available_teachers2
                if teacher_specialty.get(t, '').strip() != subject.strip()
            ]
            
            if different_specialty2:
                available_teachers2 = different_specialty2
            
            # Sort by total count
            available_teachers2.sort(key=lambda t: teacher_total_count[t])
            
            if available_teachers2:
                supervisor2 = available_teachers2[0]
                exams_df.at[idx, 'supervisor2'] = supervisor2
                teacher_daily_count[supervisor2][date_str] += 1
                teacher_total_count[supervisor2] += 1
        else:
            # Level 2: Section (Teaching Assistant)
            if sections_list:
                available_sections = [
                    s for s in sections_list
                    if section_daily_count[s][date_str] < 3
                ]
                
                # Sort by total count
                available_sections.sort(key=lambda s: section_total_count[s])
                
                if available_sections:
                    supervisor2 = available_sections[0]
                    exams_df.at[idx, 'supervisor2'] = supervisor2
                    section_daily_count[supervisor2][date_str] += 1
                    section_total_count[supervisor2] += 1
    
    return exams_df

# Sidebar
st.sidebar.title("⚙️ إعدادات المدرسة")

school_name = st.sidebar.text_input("اسم المدرسة", "مدرسة عثمان بن عفان النموذجية للبنين")
school_name_en = st.sidebar.text_input("اسم المدرسة (إنجليزي)", "Othman Bin Affan Model School for Boys")
academic_year = st.sidebar.text_input("العام الأكاديمي", "2025-2026")
semester = st.sidebar.selectbox("الفصل الدراسي", ["الفصل الدراسي الأول", "الفصل الدراسي الثاني"])

st.sidebar.markdown("---")
st.sidebar.title("📁 رفع الملفات")

teachers_file = st.sidebar.file_uploader("1️⃣ ملف المعلمات (Excel)", type=['xlsx', 'xls'], key='teachers')
sections_file = st.sidebar.file_uploader("2️⃣ ملف الشعب (Excel)", type=['xlsx', 'xls'], key='sections')
exam_file = st.sidebar.file_uploader("3️⃣ جدول الاختبارات (Excel)", type=['xlsx', 'xls'], key='exams')

# Main content
st.markdown("""
<div style='background: linear-gradient(135deg, #8B0000 0%, #A52A2A 100%); padding: 30px; border-radius: 10px; text-align: center; margin-bottom: 30px;'>
    <h1 style='color: white; margin: 0;'>📋 نظام جدول المراقبة الكامل</h1>
    <p style='color: white; font-size: 18px; margin: 10px 0 0 0;'>رفع جدول الاختبارات + توزيع تلقائي + توليد الجداول</p>
</div>
""", unsafe_allow_html=True)

def main():
    if not teachers_file or not exam_file:
        st.info("👈 يرجى رفع ملف المعلمات وجدول الاختبارات من الشريط الجانبي")
        return
    
    try:
        # Load teachers
        teachers_df = pd.read_excel(teachers_file)
        
        # Normalize column names
        column_mapping = {
            'اسم المعلم': 'teacher_name',
            'اسم المعلمة': 'teacher_name',
            'teacher_name': 'teacher_name',
            'المادة الدراسية': 'specialty',
            'التخصص': 'specialty',
            'specialty': 'specialty',
        }
        
        for old_col, new_col in column_mapping.items():
            if old_col in teachers_df.columns:
                teachers_df.rename(columns={old_col: new_col}, inplace=True)
        
        if 'teacher_name' not in teachers_df.columns:
            st.error("❌ ملف المعلمات يجب أن يحتوي على عمود 'اسم المعلم' أو 'اسم المعلمة'")
            return
        
        if 'specialty' not in teachers_df.columns:
            teachers_df['specialty'] = ''
        
        # Remove duplicates
        teachers_df = teachers_df[['teacher_name', 'specialty']].drop_duplicates()
        
        st.success(f"✅ تم تحميل {len(teachers_df)} معلمة")
        
        # Load sections (optional)
        sections_df = None
        if sections_file:
            sections_df = pd.read_excel(sections_file)
            st.success(f"✅ تم تحميل {len(sections_df)} شعبة (مساعدي معلم)")
        
        # Load and parse exam schedule
        exams_df = parse_exam_schedule(exam_file)
        st.success(f"✅ تم تحليل {len(exams_df)} اختبار")
        
        # Show data preview
        with st.expander("🔍 معاينة البيانات"):
            st.write("**المعلمات:**", teachers_df.head())
            if sections_df is not None:
                st.write("**الشعب:**", sections_df.head())
            st.write("**الاختبارات:**", exams_df.head())
        
        # Assignment button
        st.markdown("---")
        if st.button("🎯 توزيع المراقبين تلقائياً", use_container_width=True):
            with st.spinner("جاري التوزيع..."):
                exams_df = assign_supervisors_smart(exams_df, teachers_df, sections_df)
                st.session_state['assigned_exams'] = exams_df
                st.success("✅ تم التوزيع بنجاح!")
        
        # Display results
        if 'assigned_exams' in st.session_state:
            exams_df = st.session_state['assigned_exams']
            
            # Group by date
            dates = sorted(exams_df['date'].unique())
            
            st.markdown("---")
            st.header("📅 الجداول اليومية")
            
            for date in dates:
                day_exams = exams_df[exams_df['date'] == date].copy()
                day_name = get_day_name_arabic(date)
                date_str = date.strftime('%Y-%m-%d')
                
                st.subheader(f"{day_name} - {date_str}")
                
                # Display table
                display_df = day_exams[['session', 'subject', 'level', 'supervisor1', 'supervisor2']].copy()
                display_df.columns = ['الحصة', 'المادة', 'المستوى', 'المراقب 1', 'المراقب 2']
                st.dataframe(display_df, use_container_width=True)
                
                # Export buttons
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button(f"📄 تصدير Word - {day_name}", key=f"word_{date_str}"):
                        # Prepare daily schedule dict
                        daily_schedule = {
                            'date': date,
                            'day_name': day_name,
                            'exams': day_exams.to_dict('records')
                        }
                        word_file = export_to_word(
                            daily_schedule,
                            school_name,
                            academic_year,
                            f"{day_name} - {date_str}",
                            semester
                        )
                        with open(word_file, 'rb') as f:
                            st.download_button(
                                label=f"⬇️ تحميل Word - {day_name}",
                                data=f,
                                file_name=f"جدول_المراقبة_{day_name}_{date_str}.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                key=f"download_word_{date_str}"
                            )
                
                with col2:
                    if st.button(f"📕 تصدير PDF - {day_name}", key=f"pdf_{date_str}"):
                        # Prepare daily schedule dict
                        daily_schedule = {
                            'date': date,
                            'day_name': day_name,
                            'exams': day_exams.to_dict('records')
                        }
                        pdf_file = export_to_pdf_v2(
                            daily_schedule,
                            school_name,
                            academic_year,
                            f"{day_name} - {date_str}",
                            semester
                        )
                        with open(pdf_file, 'rb') as f:
                            st.download_button(
                                label=f"⬇️ تحميل PDF - {day_name}",
                                data=f,
                                file_name=f"جدول_المراقبة_{day_name}_{date_str}.pdf",
                                mime="application/pdf",
                                key=f"download_pdf_{date_str}"
                            )
                
                st.markdown("---")
        
    except Exception as e:
        st.error(f"❌ حدث خطأ: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("""
### 💡 نصائح الاستخدام

**ملف المعلمات:**
- يجب أن يحتوي على عمود `اسم المعلم`
- يمكن أن يحتوي على عمود `المادة الدراسية`

**ملف الشعب:**
- يحتوي على عمود `الصف`
- مثال: أول1، أول2، ثالث1، إلخ
- يُستخدم للمستوى الثاني فقط

**جدول الاختبارات:**
- يجب أن يحتوي على الأعمدة:
  - اليوم والتاريخ
  - الحصة الثانية
  - الحصة الثالثة والرابعة
  - المستوى

---

**تم التطوير بواسطة:** سحر عثمان  
**البريد:** Sahar.Osman@education.qa  
**المدرسة:** مدرسة عثمان بن عفان النموذجية للبنين  
**الدولة:** قطر 🇶🇦
""")

if __name__ == "__main__":
    main()

