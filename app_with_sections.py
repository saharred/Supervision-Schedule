"""
Complete Exam Supervision Schedule Generator with Sections Support V2
- Correct specialty exclusion (exclude same specialty as exam)
- Correct section matching (match section with grade level)
- Comprehensive statistics
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

def normalize_grade_name(grade_str):
    """Normalize grade names for matching"""
    grade_str = str(grade_str).strip()
    # Map variations to standard forms
    mapping = {
        'الأول': 'أول',
        'الثاني': 'ثاني',
        'الثالث': 'ثالث',
        'الرابع': 'رابع'
    }
    for old, new in mapping.items():
        grade_str = grade_str.replace(old, new)
    return grade_str

def normalize_subject_name(subject_str):
    """Normalize subject names for matching"""
    subject_str = str(subject_str).strip()
    # Remove parentheses content
    subject_str = re.sub(r'\([^)]*\)', '', subject_str).strip()
    return subject_str

def parse_exam_schedule(file):
    """Parse exam schedule from Excel file and expand by sections"""
    df = pd.read_excel(file)
    
    exams = []
    
    for _, row in df.iterrows():
        date = parse_date_arabic(row['اليوم والتاريخ'])
        if not date:
            continue
        
        level = normalize_grade_name(str(row['المستوى']).strip())
        
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
                    'subject_normalized': normalize_subject_name(subject),
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
                    'subject_normalized': normalize_subject_name(subject),
                    'level': level,
                    'grade': level,
                    'section': '',
                    'supervisor1': '',
                    'supervisor2': ''
                })
    
    return pd.DataFrame(exams)

def expand_exams_by_sections(exams_df, sections_df):
    """
    Expand each exam to multiple rows, one per section
    Example: Exam for grade 'ثالث' → 5 rows for ثالث1, ثالث2, ثالث3, ثالث4, ثالث5
    """
    if sections_df is None or len(sections_df) == 0:
        return exams_df
    
    # Extract grade from section names
    sections_df = sections_df.copy()
    sections_df['grade'] = sections_df['الصف'].str.extract(r'(أول|ثاني|ثالث|رابع)')[0]
    
    expanded_exams = []
    
    for _, exam in exams_df.iterrows():
        exam_grade = exam['grade']
        
        # Find all sections for this grade
        matching_sections = sections_df[sections_df['grade'] == exam_grade]['الصف'].tolist()
        
        if matching_sections:
            # Create one exam row per section
            for section in matching_sections:
                exam_copy = exam.copy()
                exam_copy['section'] = section
                expanded_exams.append(exam_copy)
        else:
            # No sections found, keep original
            expanded_exams.append(exam)
    
    return pd.DataFrame(expanded_exams)

def assign_supervisors_smart_v2(exams_df, teachers_df, sections_df):
    """
    Assign supervisors intelligently V2:
    - Supervisor 1: Teacher with DIFFERENT specialty (exclude same specialty)
    - Supervisor 2: 
      * Grade 1 (أول): Another teacher with different specialty
      * Grades 2-4 (ثاني، ثالث، رابع): Matching section from sections_df
    """
    
    # Prepare teachers list with normalized specialties
    teachers_df = teachers_df.copy()
    teachers_df['specialty_normalized'] = teachers_df['specialty'].apply(normalize_subject_name)
    
    teachers_list = teachers_df['teacher_name'].tolist()
    teacher_specialty = dict(zip(teachers_df['teacher_name'], teachers_df['specialty_normalized']))
    
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
        subject_normalized = exam['subject_normalized']
        level = exam['level']
        section = exam['section']
        
        # Determine if this is grade 1 (أول) or grades 2-4
        is_grade_one = 'أول' in level
        
        # === Assign Supervisor 1 (always a teacher with DIFFERENT specialty) ===
        available_teachers = [
            t for t in teachers_list
            if teacher_daily_count[t][date_str] < 3
            and teacher_specialty.get(t, '').strip() != subject_normalized.strip()  # EXCLUDE same specialty
        ]
        
        # Sort by total count (load balancing)
        available_teachers.sort(key=lambda t: teacher_total_count[t])
        
        supervisor1 = None
        if available_teachers:
            supervisor1 = available_teachers[0]
            exams_df.at[idx, 'supervisor1'] = supervisor1
            teacher_daily_count[supervisor1][date_str] += 1
            teacher_total_count[supervisor1] += 1
        
        # === Assign Supervisor 2 ===
        if is_grade_one:
            # Grade 1: Another teacher with different specialty
            available_teachers2 = [
                t for t in teachers_list
                if t != supervisor1 
                and teacher_daily_count[t][date_str] < 3
                and teacher_specialty.get(t, '').strip() != subject_normalized.strip()  # EXCLUDE same specialty
            ]
            
            # Sort by total count
            available_teachers2.sort(key=lambda t: teacher_total_count[t])
            
            if available_teachers2:
                supervisor2 = available_teachers2[0]
                exams_df.at[idx, 'supervisor2'] = supervisor2
                teacher_daily_count[supervisor2][date_str] += 1
                teacher_total_count[supervisor2] += 1
        else:
            # Grades 2-4: Use the MATCHING section
            if section and section in sections_list:
                # Assign the exact matching section
                exams_df.at[idx, 'supervisor2'] = section
                section_daily_count[section][date_str] += 1
                section_total_count[section] += 1
    
    return exams_df, teacher_total_count, section_total_count

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
        
        # Expand exams by sections
        exams_expanded_df = expand_exams_by_sections(exams_df, sections_df)
        st.info(f"📊 بعد التوسع حسب الشعب: {len(exams_expanded_df)} صف اختبار")
        
        # Distribute supervisors
        if st.button("🎯 توزيع المراقبين تلقائياً", use_container_width=True):
            with st.spinner("جاري التوزيع..."):
                result_df, teacher_counts, section_counts = assign_supervisors_smart_v2(
                    exams_expanded_df, teachers_df, sections_df
                )
                
                # Store in session state
                st.session_state['result_df'] = result_df
                st.session_state['teacher_counts'] = teacher_counts
                st.session_state['section_counts'] = section_counts
                st.session_state['teachers_df'] = teachers_df
                st.session_state['school_name'] = school_name
                st.session_state['school_name_en'] = school_name_en
                st.session_state['academic_year'] = academic_year
                st.session_state['semester'] = semester
                
                st.success("✅ تم التوزيع بنجاح!")
        
        # Display results
        if 'result_df' in st.session_state:
            result_df = st.session_state['result_df']
            teacher_counts = st.session_state['teacher_counts']
            section_counts = st.session_state['section_counts']
            
            st.markdown("---")
            st.subheader("📋 نتائج التوزيع")
            
            # Prepare display dataframe
            display_df = result_df.copy()
            display_df['التاريخ'] = display_df['date'].dt.strftime('%Y-%m-%d')
            display_df['اليوم'] = display_df['date'].apply(get_day_name_arabic)
            
            display_columns = {
                'التاريخ': display_df['التاريخ'],
                'اليوم': display_df['اليوم'],
                'الحصة': display_df['session'],
                'المادة': display_df['subject'],
                'الصف': display_df['section'],
                'المراقب الأول': display_df['supervisor1'],
                'المراقب الثاني': display_df['supervisor2']
            }
            
            display_final = pd.DataFrame(display_columns)
            st.dataframe(display_final, use_container_width=True, height=400)
            
            # Statistics
            st.markdown("---")
            st.subheader("📊 الإحصائيات")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 👩‍🏫 إحصائيات المعلمات")
                
                # Calculate percentages
                total_teacher_assignments = sum(teacher_counts.values())
                
                teacher_stats = []
                for teacher, count in sorted(teacher_counts.items(), key=lambda x: x[1], reverse=True):
                    percentage = (count / total_teacher_assignments * 100) if total_teacher_assignments > 0 else 0
                    teacher_stats.append({
                        'اسم المعلمة': teacher,
                        'عدد المراقبات': count,
                        'النسبة المئوية': f"{percentage:.1f}%"
                    })
                
                teacher_stats_df = pd.DataFrame(teacher_stats)
                st.dataframe(teacher_stats_df, use_container_width=True, height=300)
                
                st.metric("إجمالي مراقبات المعلمات", total_teacher_assignments)
            
            with col2:
                st.markdown("### 🏫 إحصائيات الشعب")
                
                if section_counts:
                    total_section_assignments = sum(section_counts.values())
                    
                    section_stats = []
                    for section, count in sorted(section_counts.items(), key=lambda x: x[1], reverse=True):
                        percentage = (count / total_section_assignments * 100) if total_section_assignments > 0 else 0
                        section_stats.append({
                            'الشعبة': section,
                            'عدد المراقبات': count,
                            'النسبة المئوية': f"{percentage:.1f}%"
                        })
                    
                    section_stats_df = pd.DataFrame(section_stats)
                    st.dataframe(section_stats_df, use_container_width=True, height=300)
                    
                    st.metric("إجمالي مراقبات الشعب", total_section_assignments)
                else:
                    st.info("لا توجد شعب في التوزيع")
            
            # Export buttons
            st.markdown("---")
            st.subheader("📥 تصدير الجداول")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📄 تصدير إلى Word", use_container_width=True):
                    with st.spinner("جاري إنشاء ملف Word..."):
                        try:
                            word_path = export_to_word(
                                result_df,
                                school_name,
                                school_name_en,
                                academic_year,
                                semester
                            )
                            
                            with open(word_path, 'rb') as f:
                                st.download_button(
                                    label="⬇️ تحميل ملف Word",
                                    data=f,
                                    file_name="جدول_المراقبة.docx",
                                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                    use_container_width=True
                                )
                        except Exception as e:
                            st.error(f"❌ خطأ في التصدير: {str(e)}")
            
            with col2:
                if st.button("📕 تصدير إلى PDF", use_container_width=True):
                    with st.spinner("جاري إنشاء ملف PDF..."):
                        try:
                            pdf_path = export_to_pdf_v2(
                                result_df,
                                school_name,
                                school_name_en,
                                academic_year,
                                semester
                            )
                            
                            with open(pdf_path, 'rb') as f:
                                st.download_button(
                                    label="⬇️ تحميل ملف PDF",
                                    data=f,
                                    file_name="جدول_المراقبة.pdf",
                                    mime="application/pdf",
                                    use_container_width=True
                                )
                        except Exception as e:
                            st.error(f"❌ خطأ في التصدير: {str(e)}")
    
    except Exception as e:
        st.error(f"❌ حدث خطأ: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

if __name__ == "__main__":
    main()

