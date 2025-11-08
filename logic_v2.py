"""
Simplified Exam Supervision Schedule Logic
Generates daily supervision schedules from exam timetable
"""

import pandas as pd
from datetime import datetime
from typing import Dict, List
import warnings
warnings.filterwarnings('ignore')


def parse_exam_schedule(exams_df):
    """
    Parse exam schedule and group by date
    Returns: dict of {date: list of exams}
    """
    exams_df = exams_df.copy()
    
    # Parse dates
    exams_df['exam_date'] = pd.to_datetime(exams_df['exam_date'])
    
    # Group by date
    daily_schedules = {}
    
    for date, group in exams_df.groupby('exam_date'):
        daily_schedules[date] = group.sort_values('start_time').to_dict('records')
    
    return daily_schedules


def get_day_name_arabic(date):
    """Get Arabic day name from date"""
    days_arabic = {
        0: 'الاثنين',
        1: 'الثلاثاء',
        2: 'الأربعاء',
        3: 'الخميس',
        4: 'الجمعة',
        5: 'السبت',
        6: 'الأحد'
    }
    return days_arabic[date.weekday()]


def format_daily_schedule(date, exams, teachers_df=None):
    """
    Format daily schedule for display and export
    
    Args:
        date: datetime object
        exams: list of exam dictionaries
        teachers_df: optional DataFrame with teacher assignments
    
    Returns:
        dict with formatted schedule data
    """
    day_name = get_day_name_arabic(date)
    date_str = date.strftime('%Y-%m-%d')
    
    # Group exams by subject and time
    schedule_data = []
    
    for exam in exams:
        subject = exam.get('subject', '')
        grade = exam.get('grade', exam.get('level', ''))
        section = exam.get('section', '')
        start_time = exam.get('start_time', '')
        end_time = exam.get('end_time', '')
        invigilators_needed = int(exam.get('invigilators_needed', 2))
        
        # Get assigned teachers if provided
        supervisor1 = exam.get('supervisor1', '')
        supervisor2 = exam.get('supervisor2', '')
        
        schedule_data.append({
            'subject': subject,
            'grade': grade,
            'section': section,
            'start_time': start_time,
            'end_time': end_time,
            'supervisor1': supervisor1,
            'supervisor2': supervisor2,
            'invigilators_needed': invigilators_needed
        })
    
    return {
        'date': date,
        'date_str': date_str,
        'day_name': day_name,
        'exams': schedule_data
    }


def create_schedule_dataframe(daily_schedule):
    """Convert daily schedule to DataFrame for display"""
    exams = daily_schedule['exams']
    
    if not exams:
        return pd.DataFrame()
    
    rows = []
    for exam in exams:
        rows.append({
            'المادة': exam['subject'],
            'الصف': exam['grade'],
            'الشعبة': exam['section'],
            'الوقت': f"{exam['start_time']} - {exam['end_time']}",
            'المراقب الأول': exam['supervisor1'],
            'المراقب الثاني': exam['supervisor2']
        })
    
    return pd.DataFrame(rows)


def validate_exam_file(df):
    """
    Validate exam schedule file
    Returns: (is_valid, error_message)
    """
    required_cols = ['exam_date', 'start_time', 'end_time', 'subject']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        return False, f"أعمدة مفقودة: {', '.join(missing_cols)}"
    
    # Check for grade or level column
    if 'grade' not in df.columns and 'level' not in df.columns:
        return False, "يجب وجود عمود 'grade' أو 'level'"
    
    return True, ""


def get_unique_dates(exams_df):
    """Get sorted list of unique exam dates"""
    exams_df = exams_df.copy()
    exams_df['exam_date'] = pd.to_datetime(exams_df['exam_date'])
    dates = sorted(exams_df['exam_date'].unique())
    return dates

