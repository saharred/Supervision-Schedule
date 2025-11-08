"""
Simplified Exam Supervision Schedule Generator
Generates daily schedules in Word and PDF formats
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import io

# Import custom modules
from logic_v2 import (
    parse_exam_schedule, format_daily_schedule, create_schedule_dataframe,
    validate_exam_file, get_unique_dates, get_day_name_arabic
)
from export_word import export_to_word
from export_pdf_v2 import export_to_pdf_v2

# Page configuration
st.set_page_config(
    page_title="جدول المراقبة للاختبارات",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for RTL and Arabic styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Tajawal', 'Tahoma', sans-serif;
        direction: rtl;
        text-align: right;
    }
    
    .stDataFrame {
        direction: rtl;
    }
    
    .stDataFrame table {
        direction: rtl;
        text-align: right;
    }
    
    .stDataFrame th {
        background-color: #8B0000 !important;
        color: white !important;
        text-align: right !important;
        font-weight: bold;
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
    
    .success-box {
        background-color: #d4edda;
        border-right: 5px solid #28a745;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    
    .info-box {
        background-color: #d1ecf1;
        border-right: 5px solid #0c5460;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)


def main():
    # Header
    st.markdown("""
    <div style='text-align: center; padding: 20px; background: linear-gradient(135deg, #8B0000 0%, #A52A2A 100%); border-radius: 10px; margin-bottom: 30px;'>
        <h1 style='color: white; margin: 0;'>📋 جدول المراقبة للاختبارات</h1>
        <p style='color: #f0f0f0; margin: 10px 0 0 0;'>نظام توليد جداول المراقبة اليومية - Word & PDF</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ إعدادات المدرسة")
        school_name = st.text_input("اسم المدرسة", value="مدرسة عثمان بن عفان النموذجية للبنين")
        academic_year = st.text_input("العام الأكاديمي", value="2025-2026")
        semester = st.selectbox("الفصل الدراسي", ["الفصل الدراسي الأول", "الفصل الدراسي الثاني"])
        level_name = st.text_input("المستوى/المرحلة", value="اللغة العربية - اللغة الإنجليزية")
        
        st.markdown("---")
        st.header("📁 رفع ملف الاختبارات")
        
        # Upload exams file
        exams_file = st.file_uploader(
            "ملف جدول الاختبارات (Excel)",
            type=['xlsx', 'xls'],
            help="يجب أن يحتوي على: exam_date, start_time, end_time, subject, grade, section, supervisor1, supervisor2"
        )
        
        st.markdown("---")
        st.markdown("""
        <div style='background-color: #f8f9fa; padding: 15px; border-radius: 5px;'>
            <h4 style='color: #8B0000; margin-top: 0;'>💡 نصائح الاستخدام</h4>
            <ul style='font-size: 13px; line-height: 1.8;'>
                <li>ارفع ملف واحد فقط (جدول الاختبارات)</li>
                <li>يجب أن يحتوي على أسماء المراقبين</li>
                <li>سيتم توليد جدول منفصل لكل يوم</li>
                <li>تصدير Word قابل للتعديل</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Main content
    if not exams_file:
        st.info("👈 يرجى رفع ملف جدول الاختبارات من الشريط الجانبي للبدء")
        
        # Show sample format
        with st.expander("📖 عرض تنسيق الملف المطلوب"):
            st.subheader("ملف جدول الاختبارات")
            sample_exams = pd.DataFrame({
                'exam_date': ['2025-01-08', '2025-01-08', '2025-01-09'],
                'start_time': ['08:00', '10:00', '08:00'],
                'end_time': ['10:00', '12:00', '10:00'],
                'subject': ['اللغة العربية', 'اللغة الإنجليزية', 'الرياضيات'],
                'grade': ['ثالث', 'رابع', 'ثالث'],
                'section': ['1', '1', '2'],
                'supervisor1': ['ياسمين محمد', 'حمدة الشمري', 'فاطمة أحمد'],
                'supervisor2': ['ريحاب محمد', 'أسماء الدحيج', 'نورة علي']
            })
            st.dataframe(sample_exams, use_container_width=True)
            
            st.markdown("""
            **الأعمدة المطلوبة:**
            - `exam_date`: تاريخ الاختبار (YYYY-MM-DD)
            - `start_time`: وقت البدء (HH:MM)
            - `end_time`: وقت النهاية (HH:MM)
            - `subject`: المادة
            - `grade`: الصف (أو `level` للمستوى)
            - `section`: الشعبة
            - `supervisor1`: المراقب الأول
            - `supervisor2`: المراقب الثاني
            """)
        
        return
    
    # Load data
    try:
        exams_df = pd.read_excel(exams_file)
        st.success(f"✅ تم تحميل {len(exams_df)} اختبار")
        
    except Exception as e:
        st.error(f"❌ خطأ في قراءة الملف: {str(e)}")
        return
    
    # Validate file
    is_valid, error_msg = validate_exam_file(exams_df)
    if not is_valid:
        st.error(f"❌ {error_msg}")
        return
    
    # Show data preview
    with st.expander("👀 معاينة البيانات المحملة"):
        st.dataframe(exams_df.head(10), use_container_width=True)
    
    # Get unique dates
    exam_dates = get_unique_dates(exams_df)
    
    if not exam_dates:
        st.error("❌ لم يتم العثور على تواريخ اختبارات صحيحة")
        return
    
    st.markdown("---")
    st.markdown(f"### 📅 تم العثور على {len(exam_dates)} يوم اختبار")
    
    # Parse schedule
    daily_schedules = parse_exam_schedule(exams_df)
    
    # Display each day
    for date in exam_dates:
        day_name = get_day_name_arabic(date)
        date_str = date.strftime('%Y-%m-%d')
        
        st.markdown(f"""
        <div class='day-card'>
            <h2 style='margin: 0; color: white;'>{day_name} - {date_str}</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # Format daily schedule
        daily_schedule = format_daily_schedule(date, daily_schedules[date])
        
        # Display schedule table
        schedule_df = create_schedule_dataframe(daily_schedule)
        
        if not schedule_df.empty:
            st.dataframe(schedule_df, use_container_width=True)
            
            # Export buttons
            col1, col2 = st.columns(2)
            
            with col1:
                # Export to Word
                try:
                    word_buffer = export_to_word(
                        daily_schedule,
                        school_name=school_name,
                        academic_year=academic_year,
                        level_name=level_name,
                        semester=semester
                    )
                    
                    filename_word = f"جدول_المراقبة_{day_name}_{date_str}.docx"
                    
                    st.download_button(
                        label="📥 تصدير Word (قابل للتعديل)",
                        data=word_buffer,
                        file_name=filename_word,
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True,
                        key=f"word_{date_str}"
                    )
                except Exception as e:
                    st.error(f"خطأ في تصدير Word: {str(e)}")
            
            with col2:
                # Export to PDF
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
    
    # Footer
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p>تم التطوير بواسطة: <strong>سحر عثمان</strong> - منسقة المشاريع الإلكترونية</p>
        <p>مدرسة عثمان بن عفان النموذجية للبنين - وزارة التعليم والتعليم العالي - دولة قطر 🇶🇦</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()

