"""
Exam Supervision Schedule Generator
جدول المراقبة للاختبارات
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import io

# Import custom modules
from logic import distribute_invigilators, assignments_to_dataframe, get_statistics
from export import export_to_excel, export_to_pdf

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
    
    .metric-card {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border-right: 5px solid #8B0000;
        margin: 10px 0;
    }
    
    .warning-box {
        background-color: #fff3cd;
        border-right: 5px solid #ffc107;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
    
    .success-box {
        background-color: #d4edda;
        border-right: 5px solid #28a745;
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
        <p style='color: #f0f0f0; margin: 10px 0 0 0;'>نظام توزيع تلقائي ذكي للمراقبات</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ إعدادات المدرسة")
        school_name = st.text_input("اسم المدرسة", value="مدرسة عثمان بن عفان النموذجية")
        
        st.markdown("---")
        st.header("📁 رفع الملفات")
        
        # Upload teachers file
        teachers_file = st.file_uploader(
            "ملف المعلمات (teachers.xlsx)",
            type=['xlsx', 'xls'],
            help="يجب أن يحتوي على: teacher_name, specialty, max_per_day, unavailable"
        )
        
        # Upload exams file
        exams_file = st.file_uploader(
            "ملف الاختبارات (exams.xlsx)",
            type=['xlsx', 'xls'],
            help="يجب أن يحتوي على: exam_date, start_time, end_time, subject, grade, section, invigilators_needed"
        )
        
        st.markdown("---")
        st.markdown("""
        <div style='background-color: #f8f9fa; padding: 15px; border-radius: 5px;'>
            <h4 style='color: #8B0000; margin-top: 0;'>💡 نصائح الاستخدام</h4>
            <ul style='font-size: 13px; line-height: 1.8;'>
                <li>تأكد من صحة تنسيق الملفات</li>
                <li>التواريخ بصيغة YYYY-MM-DD</li>
                <li>الأوقات بصيغة HH:MM</li>
                <li>يمكن تعديل الجدول يدوياً بعد التوليد</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Main content
    if not teachers_file or not exams_file:
        st.info("👈 يرجى رفع ملفي المعلمات والاختبارات من الشريط الجانبي للبدء")
        
        # Show sample format
        with st.expander("📖 عرض تنسيق الملفات المطلوبة"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("ملف المعلمات (teachers.xlsx)")
                sample_teachers = pd.DataFrame({
                    'teacher_name': ['فاطمة أحمد', 'نورة محمد', 'سارة علي'],
                    'specialty': ['رياضيات', 'عربي', 'علوم'],
                    'max_per_day': [3, 2, 3],
                    'unavailable': ['', '2025-01-15', '']
                })
                st.dataframe(sample_teachers, use_container_width=True)
            
            with col2:
                st.subheader("ملف الاختبارات (exams.xlsx)")
                sample_exams = pd.DataFrame({
                    'exam_date': ['2025-01-10', '2025-01-10'],
                    'start_time': ['08:00', '10:00'],
                    'end_time': ['10:00', '12:00'],
                    'subject': ['رياضيات', 'عربي'],
                    'grade': ['الثالث', 'الرابع'],
                    'section': ['1', '2'],
                    'invigilators_needed': [2, 2]
                })
                st.dataframe(sample_exams, use_container_width=True)
        
        return
    
    # Load data
    try:
        teachers_df = pd.read_excel(teachers_file)
        exams_df = pd.read_excel(exams_file)
        
        st.success(f"✅ تم تحميل {len(teachers_df)} معلمة و {len(exams_df)} اختبار")
        
    except Exception as e:
        st.error(f"❌ خطأ في قراءة الملفات: {str(e)}")
        return
    
    # Validate columns
    required_teacher_cols = ['teacher_name', 'specialty', 'max_per_day']
    required_exam_cols = ['exam_date', 'start_time', 'end_time', 'subject', 'grade', 'section', 'invigilators_needed']
    
    missing_teacher = [col for col in required_teacher_cols if col not in teachers_df.columns]
    missing_exam = [col for col in required_exam_cols if col not in exams_df.columns]
    
    if missing_teacher or missing_exam:
        st.error("❌ أعمدة مفقودة في الملفات:")
        if missing_teacher:
            st.write(f"ملف المعلمات: {', '.join(missing_teacher)}")
        if missing_exam:
            st.write(f"ملف الاختبارات: {', '.join(missing_exam)}")
        return
    
    # Show data preview
    with st.expander("👀 معاينة البيانات المحملة"):
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("المعلمات")
            st.dataframe(teachers_df.head(), use_container_width=True)
        with col2:
            st.subheader("الاختبارات")
            st.dataframe(exams_df.head(), use_container_width=True)
    
    # Distribution button
    st.markdown("---")
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        distribute_btn = st.button("🎯 توزيع تلقائي", use_container_width=True)
    
    # Perform distribution
    if distribute_btn or 'assignments' in st.session_state:
        if distribute_btn:
            with st.spinner("⏳ جاري التوزيع التلقائي..."):
                assignments, warnings = distribute_invigilators(teachers_df, exams_df)
                st.session_state['assignments'] = assignments
                st.session_state['warnings'] = warnings
                st.session_state['result_df'] = assignments_to_dataframe(assignments)
        
        assignments = st.session_state.get('assignments', [])
        warnings = st.session_state.get('warnings', [])
        result_df = st.session_state.get('result_df', pd.DataFrame())
        
        if not result_df.empty:
            # Statistics
            stats = get_statistics(assignments, teachers_df)
            
            st.markdown("### 📊 إحصائيات التوزيع")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class='metric-card'>
                    <h3 style='margin: 0; color: #8B0000;'>{stats['total_assignments']}</h3>
                    <p style='margin: 5px 0 0 0; color: #666;'>إجمالي المراقبات</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class='metric-card'>
                    <h3 style='margin: 0; color: #8B0000;'>{stats['different_specialty_pct']:.1f}%</h3>
                    <p style='margin: 5px 0 0 0; color: #666;'>تخصص مختلف</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class='metric-card'>
                    <h3 style='margin: 0; color: #8B0000;'>{stats['max_load']}</h3>
                    <p style='margin: 5px 0 0 0; color: #666;'>أعلى حمل</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                <div class='metric-card'>
                    <h3 style='margin: 0; color: #8B0000;'>{stats['min_load']}</h3>
                    <p style='margin: 5px 0 0 0; color: #666;'>أقل حمل</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Warnings
            if warnings:
                st.markdown("### ⚠️ تنبيهات")
                for warning in warnings:
                    st.markdown(f"""
                    <div class='warning-box'>
                        <strong>{warning['subject']} - {warning['grade_section']}</strong><br>
                        التاريخ: {warning['exam_date']}<br>
                        {warning['message']}
                    </div>
                    """, unsafe_allow_html=True)
            
            # Display result
            st.markdown("---")
            st.markdown("### 📋 الجدول النهائي")
            
            # Editable dataframe
            edited_df = st.data_editor(
                result_df,
                use_container_width=True,
                num_rows="dynamic",
                hide_index=True
            )
            
            # Export buttons
            st.markdown("---")
            st.markdown("### 💾 تصدير الجدول")
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                # Excel export
                excel_data = export_to_excel(edited_df)
                if excel_data:
                    st.download_button(
                        label="📥 تصدير Excel",
                        data=excel_data,
                        file_name=f"supervision_schedule_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
            
            with col2:
                # PDF export
                pdf_data = export_to_pdf(edited_df, school_name=school_name)
                if pdf_data:
                    st.download_button(
                        label="📄 تصدير PDF",
                        data=pdf_data,
                        file_name=f"supervision_schedule_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
        else:
            st.warning("⚠️ لم يتم إنشاء أي توزيع. تحقق من البيانات المدخلة.")


if __name__ == "__main__":
    main()

