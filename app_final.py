"""
Complete Exam Supervision Schedule Generator
Automatically assigns supervisors and generates daily schedules
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import re
from collections import defaultdict

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
        text-align: right;
    }
    
    .day-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 15px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


def parse_date_arabic(date_str):
    """Parse Arabic date string to datetime"""
    # Extract date in format YYYY/MM/DD
    match = re.search(r'(\d{4})/(\d{1,2})/(\d{1,2})', date_str)
    if match:
        year, month, day = match.groups()
        return datetime(int(year), int(month), int(day))
    return None


def assign_supervisors_auto(exams_df, teachers_df):
    """
    Automatically assign supervisors to exams
    
    Strategy:
    1. Prefer teachers with different specialty than exam subject
    2. Balance workload across all teachers
    3. Avoid same teacher supervising same subject
    """
    # Track teacher assignments per day
    teacher_assignments = defaultdict(lambda: defaultdict(int))
    
    # Prepare teachers list
    teachers_list = teachers_df.to_dict('records')
    
    # Assign supervisors for each exam
    for idx, exam in exams_df.iterrows():
        date = exam['date']
        subject = exam['subject']
        
        # Find available teachers (prefer different specialty)
        available_teachers = []
        for teacher in teachers_list:
            teacher_name = teacher['teacher_name']
            teacher_specialty = teacher.get('specialty', '')
            
            # Check if teacher is not overloaded this day
            if teacher_assignments[date][teacher_name] < 3:  # Max 3 per day
                # Prefer teachers with different specialty
                if teacher_specialty != subject:
                    available_teachers.append((teacher_name, 0))  # Priority 0
                else:
                    available_teachers.append((teacher_name, 1))  # Priority 1
        
        # Sort by priority and current workload
        available_teachers.sort(key=lambda x: (x[1], teacher_assignments[date][x[0]]))
        
        # Assign 2 supervisors
        if len(available_teachers) >= 2:
            supervisor1 = available_teachers[0][0]
            supervisor2 = available_teachers[1][0]
            
            exams_df.at[idx, 'supervisor1'] = supervisor1
            exams_df.at[idx, 'supervisor2'] = supervisor2
            
            teacher_assignments[date][supervisor1] += 1
            teacher_assignments[date][supervisor2] += 1
        elif len(available_teachers) == 1:
            exams_df.at[idx, 'supervisor1'] = available_teachers[0][0]
            exams_df.at[idx, 'supervisor2'] = ''
        else:
            exams_df.at[idx, 'supervisor1'] = ''
            exams_df.at[idx, 'supervisor2'] = ''
    
    return exams_df


def parse_exam_schedule(exam_file):
    """Parse exam schedule from Excel file"""
    df = pd.read_excel(exam_file)
    
    # Parse dates
    df['date'] = df['اليوم والتاريخ'].apply(parse_date_arabic)
    
    # Extract subjects from columns
    exams_list = []
    
    for _, row in df.iterrows():
        date = row['date']
        level = row['المستوى']
        
        # Session 2
        subject2 = row['الحصة الثانية']
        if pd.notna(subject2) and subject2 != 'لا يوجد احتبار':
            exams_list.append({
                'date': date,
                'session': 'الحصة الثانية',
                'start_time': '08:00',
                'end_time': '10:00',
                'subject': subject2,
                'level': level,
                'grade': level,
                'section': '',
                'supervisor1': '',
                'supervisor2': ''
            })
        
        # Session 3&4
        subject34 = row['الحصة الثالثة والرابعة']
        if pd.notna(subject34) and subject34 != 'لا يوجد احتبار':
            exams_list.append({
                'date': date,
                'session': 'الحصة الثالثة والرابعة',
                'start_time': '10:30',
                'end_time': '12:30',
                'subject': subject34,
                'level': level,
                'grade': level,
                'section': '',
                'supervisor1': '',
                'supervisor2': ''
            })
    
    return pd.DataFrame(exams_list)


def main():
    # Header
    st.markdown("""
    <div style='text-align: center; padding: 20px; background: linear-gradient(135deg, #8B0000 0%, #A52A2A 100%); border-radius: 10px; margin-bottom: 30px;'>
        <h1 style='color: white; margin: 0;'>📋 نظام جدول المراقبة الكامل</h1>
        <p style='color: #f0f0f0; margin: 10px 0 0 0;'>رفع جدول الاختبارات + توزيع تلقائي + توليد الجداول</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ إعدادات المدرسة")
        school_name = st.text_input("اسم المدرسة", value="مدرسة عثمان بن عفان النموذجية للبنين")
        academic_year = st.text_input("العام الأكاديمي", value="2025-2026")
        semester = st.selectbox("الفصل الدراسي", ["الفصل الدراسي الأول", "الفصل الدراسي الثاني"])
        
        st.markdown("---")
        st.header("📁 رفع الملفات")
        
        # Upload teachers file
        teachers_file = st.file_uploader(
            "1️⃣ ملف المعلمات (Excel)",
            type=['xlsx', 'xls'],
            help="يجب أن يحتوي على: teacher_name, specialty"
        )
        
        # Upload exam schedule
        exam_file = st.file_uploader(
            "2️⃣ جدول الاختبارات (Excel)",
            type=['xlsx', 'xls'],
            help="جدول الاختبارات الرسمي من الوزارة"
        )
        
        st.markdown("---")
        st.markdown("""
        <div style='background-color: #f8f9fa; padding: 15px; border-radius: 5px;'>
            <h4 style='color: #8B0000; margin-top: 0;'>💡 كيف يعمل النظام</h4>
            <ol style='font-size: 13px; line-height: 1.8;'>
                <li>ارفع ملف المعلمات</li>
                <li>ارفع جدول الاختبارات</li>
                <li>النظام يوزع المراقبين تلقائياً</li>
                <li>يولد جداول يومية (Word + PDF)</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
    
    # Main content
    if not teachers_file or not exam_file:
        st.info("👈 يرجى رفع ملف المعلمات وجدول الاختبارات من الشريط الجانبي")
        return
    
    try:
        # Load teachers
        teachers_df = pd.read_excel(teachers_file)
        st.success(f"✅ تم تحميل {len(teachers_df)} معلمة")
        
        # Load and parse exam schedule
        exams_df = parse_exam_schedule(exam_file)
        st.success(f"✅ تم تحليل {len(exams_df)} اختبار")
        
        # Show preview
        with st.expander("👀 معاينة البيانات"):
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("المعلمات")
                st.dataframe(teachers_df.head(), use_container_width=True)
            with col2:
                st.subheader("الاختبارات")
                st.dataframe(exams_df.head(), use_container_width=True)
        
        # Assign supervisors
        st.markdown("---")
        if st.button("🎯 توزيع المراقبين تلقائياً", use_container_width=True):
            with st.spinner("جاري توزيع المراقبين..."):
                exams_df = assign_supervisors_auto(exams_df, teachers_df)
                st.session_state['exams_assigned'] = exams_df
                st.success("✅ تم توزيع المراقبين بنجاح!")
        
        # Show assigned exams
        if 'exams_assigned' in st.session_state:
            exams_df = st.session_state['exams_assigned']
            
            st.markdown("---")
            st.markdown("### 📅 الجداول اليومية")
            
            # Group by date
            dates = sorted(exams_df['date'].unique())
            
            for date in dates:
                day_name = get_day_name_arabic(date)
                date_str = date.strftime('%Y-%m-%d')
                
                st.markdown(f"""
                <div class='day-card'>
                    <h2 style='margin: 0; color: white;'>{day_name} - {date_str}</h2>
                </div>
                """, unsafe_allow_html=True)
                
                # Get exams for this date
                day_exams = exams_df[exams_df['date'] == date].copy()
                
                # Display table
                display_df = day_exams[['subject', 'level', 'session', 'supervisor1', 'supervisor2']].copy()
                display_df.columns = ['المادة', 'المستوى', 'الحصة', 'المراقب الأول', 'المراقب الثاني']
                st.dataframe(display_df, use_container_width=True)
                
                # Format for export
                daily_schedule = {
                    'date': date,
                    'date_str': date_str,
                    'day_name': day_name,
                    'exams': day_exams.to_dict('records')
                }
                
                # Export buttons
                col1, col2 = st.columns(2)
                
                with col1:
                    try:
                        # Determine level name for this day
                        levels = day_exams['level'].unique()
                        level_name = ' و '.join(levels)
                        
                        word_buffer = export_to_word(
                            daily_schedule,
                            school_name=school_name,
                            academic_year=academic_year,
                            level_name=level_name,
                            semester=semester
                        )
                        
                        filename_word = f"جدول_المراقبة_{day_name}_{date_str}.docx"
                        
                        st.download_button(
                            label="📥 تصدير Word",
                            data=word_buffer,
                            file_name=filename_word,
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            use_container_width=True,
                            key=f"word_{date_str}"
                        )
                    except Exception as e:
                        st.error(f"خطأ في تصدير Word: {str(e)}")
                
                with col2:
                    try:
                        pdf_buffer = export_to_pdf_v2(
                            daily_schedule,
                            school_name=school_name,
                            academic_year=academic_year,
                            level_name=level_name,
                            semester=semester
                        )
                        
                        filename_pdf = f"جدول_المراقبة_{day_name}_{date_str}.pdf"
                        
                        st.download_button(
                            label="📄 تصدير PDF",
                            data=pdf_buffer,
                            file_name=filename_pdf,
                            mime="application/pdf",
                            use_container_width=True,
                            key=f"pdf_{date_str}"
                        )
                    except Exception as e:
                        st.error(f"خطأ في تصدير PDF: {str(e)}")
                
                st.markdown("---")
    
    except Exception as e:
        st.error(f"❌ خطأ: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
    
    # Footer
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p>تم التطوير بواسطة: <strong>سحر عثمان</strong> - منسقة المشاريع الإلكترونية</p>
        <p>مدرسة عثمان بن عفان النموذجية للبنين - وزارة التعليم والتعليم العالي - دولة قطر 🇶🇦</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()

