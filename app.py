"""
Exam Supervision Schedule Generator
جدول المراقبة للاختبارات
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import io

# Import custom modules
from logic import distribute_invigilators, assignments_to_dataframe, get_statistics, get_available_levels
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
    
    .level-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin: 10px 0;
        cursor: pointer;
        transition: transform 0.2s;
    }
    
    .level-card:hover {
        transform: scale(1.02);
    }
</style>
""", unsafe_allow_html=True)


def main():
    # Header
    st.markdown("""
    <div style='text-align: center; padding: 20px; background: linear-gradient(135deg, #8B0000 0%, #A52A2A 100%); border-radius: 10px; margin-bottom: 30px;'>
        <h1 style='color: white; margin: 0;'>📋 جدول المراقبة للاختبارات</h1>
        <p style='color: #f0f0f0; margin: 10px 0 0 0;'>نظام توزيع تلقائي ذكي للمراقبات حسب المستوى الدراسي</p>
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
            help="يجب أن يحتوي على: exam_date, start_time, end_time, subject, level, section, invigilators_needed"
        )
        
        st.markdown("---")
        st.markdown("""
        <div style='background-color: #f8f9fa; padding: 15px; border-radius: 5px;'>
            <h4 style='color: #8B0000; margin-top: 0;'>💡 نصائح الاستخدام</h4>
            <ul style='font-size: 13px; line-height: 1.8;'>
                <li>استخدم عمود "level" للمستوى الدراسي</li>
                <li>التواريخ بصيغة YYYY-MM-DD</li>
                <li>الأوقات بصيغة HH:MM</li>
                <li>النظام يولد جدول منفصل لكل مستوى</li>
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
                    'specialty': ['رياضيات', 'اللغة العربية', 'العلوم'],
                    'max_per_day': [3, 2, 3],
                    'unavailable': ['', '2025-01-15', '']
                })
                st.dataframe(sample_teachers, use_container_width=True)
            
            with col2:
                st.subheader("ملف الاختبارات (exams.xlsx)")
                sample_exams = pd.DataFrame({
                    'exam_date': ['2025-01-10', '2025-01-10', '2025-01-11'],
                    'start_time': ['08:00', '08:00', '08:00'],
                    'end_time': ['10:00', '10:00', '10:00'],
                    'subject': ['الرياضيات', 'العلوم', 'اللغة العربية'],
                    'level': ['المستوى الأول', 'المستوى الثاني', 'المستوى الأول'],
                    'section': ['1', '1', '2'],
                    'invigilators_needed': [2, 2, 2]
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
    required_exam_cols = ['exam_date', 'start_time', 'end_time', 'subject', 'level', 'section', 'invigilators_needed']
    
    missing_teacher = [col for col in required_teacher_cols if col not in teachers_df.columns]
    missing_exam = [col for col in required_exam_cols if col not in exams_df.columns]
    
    if missing_teacher or missing_exam:
        st.error("❌ أعمدة مفقودة في الملفات:")
        if missing_teacher:
            st.write(f"ملف المعلمات: {', '.join(missing_teacher)}")
        if missing_exam:
            st.write(f"ملف الاختبارات: {', '.join(missing_exam)}")
        return
    
    # Get available levels
    available_levels = get_available_levels(exams_df)
    
    if not available_levels:
        st.error("❌ لم يتم العثور على مستويات دراسية في ملف الاختبارات. تأكد من وجود عمود 'level'")
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
    
    # Level selection
    st.markdown("---")
    st.markdown("### 📚 اختر المستوى الدراسي لتوليد جدول المراقبة")
    
    # Display levels as cards
    cols = st.columns(min(len(available_levels), 4))
    selected_level = None
    
    for idx, level in enumerate(available_levels):
        with cols[idx % len(cols)]:
            if st.button(f"📖 {level}", key=f"level_{idx}", use_container_width=True):
                selected_level = level
                st.session_state['selected_level'] = level
    
    # Get selected level from session state if exists
    if 'selected_level' in st.session_state:
        selected_level = st.session_state['selected_level']
    
    if not selected_level:
        st.info("👆 اختر مستوى دراسي لتوليد جدول المراقبة الخاص به")
        return
    
    # Show selected level
    st.markdown(f"""
    <div class='success-box'>
        <h3 style='margin: 0;'>✅ المستوى المختار: {selected_level}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Distribution button
    st.markdown("---")
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        distribute_btn = st.button("🎯 توزيع تلقائي", use_container_width=True)
    
    # Perform distribution
    if distribute_btn or (f'assignments_{selected_level}' in st.session_state):
        if distribute_btn:
            with st.spinner(f"⏳ جاري التوزيع التلقائي للمستوى: {selected_level}..."):
                assignments, warnings = distribute_invigilators(teachers_df, exams_df, selected_level)
                st.session_state[f'assignments_{selected_level}'] = assignments
                st.session_state[f'warnings_{selected_level}'] = warnings
                st.session_state[f'result_df_{selected_level}'] = assignments_to_dataframe(assignments)
        
        assignments = st.session_state.get(f'assignments_{selected_level}', [])
        warnings = st.session_state.get(f'warnings_{selected_level}', [])
        result_df = st.session_state.get(f'result_df_{selected_level}', pd.DataFrame())
        
        if result_df.empty:
            st.warning(f"⚠️ لا توجد اختبارات للمستوى: {selected_level}")
            return
        
        # Statistics
        stats = get_statistics(assignments, teachers_df)
        
        st.markdown(f"### 📊 إحصائيات التوزيع - {selected_level}")
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
                    <strong>{warning['message']}</strong><br>
                    التاريخ: {warning['exam_date']}<br>
                    الوقت: {warning['time']}<br>
                    المادة: {warning['subject']}<br>
                    المستوى والشعبة: {warning['level_section']}
                </div>
                """, unsafe_allow_html=True)
        
        # Display result table
        st.markdown(f"### 📋 جدول المراقبة - {selected_level}")
        st.dataframe(result_df, use_container_width=True, height=400)
        
        # Teacher load distribution
        with st.expander("📊 توزيع الأحمال على المعلمات"):
            teacher_counts = stats['teacher_counts']
            load_df = pd.DataFrame({
                'اسم المعلمة': list(teacher_counts.keys()),
                'عدد المراقبات': list(teacher_counts.values())
            }).sort_values('عدد المراقبات', ascending=False)
            
            st.dataframe(load_df, use_container_width=True)
            
            # Simple bar chart
            st.bar_chart(load_df.set_index('اسم المعلمة'))
        
        # Export options
        st.markdown("---")
        st.markdown("### 💾 تصدير الجدول")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Export to Excel
            excel_buffer = export_to_excel(result_df, school_name, selected_level)
            st.download_button(
                label="📥 تصدير Excel",
                data=excel_buffer,
                file_name=f"جدول_المراقبة_{selected_level}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        
        with col2:
            # Export to PDF
            pdf_buffer = export_to_pdf(result_df, school_name, selected_level)
            st.download_button(
                label="📄 تصدير PDF",
                data=pdf_buffer,
                file_name=f"جدول_المراقبة_{selected_level}_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p>تم التطوير بواسطة: <strong>سحر عثمان</strong> - منسقة المشاريع الإلكترونية</p>
        <p>مدرسة عثمان بن عفان النموذجية للبنين - وزارة التعليم والتعليم العالي - دولة قطر 🇶🇦</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()

