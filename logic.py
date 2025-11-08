"""
Exam Invigilation Distribution Logic
Handles automatic assignment of teachers to exam supervision slots
"""

import pandas as pd
from datetime import datetime, time
from typing import List, Dict, Tuple
import warnings
warnings.filterwarnings('ignore')


def parse_time(time_str):
    """Parse time string to time object"""
    if pd.isna(time_str):
        return None
    if isinstance(time_str, time):
        return time_str
    try:
        return datetime.strptime(str(time_str).strip(), "%H:%M").time()
    except:
        return None


def check_time_conflict(exam1_start, exam1_end, exam2_start, exam2_end):
    """Check if two time slots overlap"""
    if any(t is None for t in [exam1_start, exam1_end, exam2_start, exam2_end]):
        return False
    
    # Convert to comparable format
    return not (exam1_end <= exam2_start or exam2_end <= exam1_start)


def calculate_teacher_load(assignments, teacher_name):
    """Calculate total assignments for a teacher"""
    return len([a for a in assignments if a.get('teacher_name') == teacher_name])


def calculate_daily_load(assignments, teacher_name, exam_date):
    """Calculate assignments for a teacher on a specific date"""
    return len([a for a in assignments 
                if a.get('teacher_name') == teacher_name 
                and a.get('exam_date') == exam_date])


def is_teacher_available(teacher, exam_date, start_time, end_time, assignments):
    """Check if teacher is available for the time slot"""
    # Check unavailable dates/times
    unavailable = str(teacher.get('unavailable', '')).strip()
    if unavailable and unavailable != 'nan':
        # Simple check - can be enhanced
        if str(exam_date) in unavailable:
            return False
    
    # Check for time conflicts with existing assignments
    for assignment in assignments:
        if assignment.get('teacher_name') == teacher['teacher_name']:
            if assignment.get('exam_date') == exam_date:
                assigned_start = assignment.get('start_time')
                assigned_end = assignment.get('end_time')
                if check_time_conflict(start_time, end_time, assigned_start, assigned_end):
                    return False
    
    return True


def get_eligible_teachers(teachers_df, exam_subject, exam_date, start_time, end_time, 
                          assignments, max_daily_limit=True):
    """
    Get list of eligible teachers sorted by priority:
    1. Different specialty (preferred)
    2. Same specialty (fallback)
    3. Load balanced (fewer assignments first)
    """
    eligible = []
    
    for _, teacher in teachers_df.iterrows():
        teacher_name = teacher['teacher_name']
        specialty = str(teacher.get('specialty', '')).strip()
        max_per_day = int(teacher.get('max_per_day', 999))
        
        # Check availability
        if not is_teacher_available(teacher, exam_date, start_time, end_time, assignments):
            continue
        
        # Check daily limit
        if max_daily_limit:
            daily_load = calculate_daily_load(assignments, teacher_name, exam_date)
            if daily_load >= max_per_day:
                continue
        
        # Calculate priority
        total_load = calculate_teacher_load(assignments, teacher_name)
        is_different_specialty = (specialty.lower() != exam_subject.lower())
        
        eligible.append({
            'teacher_name': teacher_name,
            'specialty': specialty,
            'is_different_specialty': is_different_specialty,
            'total_load': total_load,
            'daily_load': calculate_daily_load(assignments, teacher_name, exam_date)
        })
    
    # Sort by priority: different specialty first, then by load
    eligible.sort(key=lambda x: (
        not x['is_different_specialty'],  # False (different) comes before True (same)
        x['total_load'],                   # Lower load first
        x['teacher_name']                  # Alphabetical as tiebreaker
    ))
    
    return eligible


def get_available_levels(exams_df):
    """
    Extract unique levels from exams dataframe
    Returns: list of level names
    """
    if 'level' not in exams_df.columns:
        return []
    
    levels = exams_df['level'].dropna().unique().tolist()
    levels = [str(level).strip() for level in levels if str(level).strip()]
    return sorted(levels)


def distribute_invigilators(teachers_df, exams_df, selected_level=None):
    """
    Main distribution algorithm
    Returns: (assignments_list, warnings_list)
    
    Args:
        teachers_df: DataFrame with teacher information
        exams_df: DataFrame with exam schedule
        selected_level: Optional - filter exams by level (e.g., 'المستوى الأول')
    """
    assignments = []
    warnings_list = []
    
    # Sort exams by date and time
    exams_df = exams_df.copy()
    
    # Filter by level if specified
    if selected_level and 'level' in exams_df.columns:
        exams_df = exams_df[exams_df['level'].str.strip() == selected_level.strip()]
    
    exams_df['exam_date'] = pd.to_datetime(exams_df['exam_date'])
    exams_df['start_time'] = exams_df['start_time'].apply(parse_time)
    exams_df['end_time'] = exams_df['end_time'].apply(parse_time)
    exams_df = exams_df.sort_values(['exam_date', 'start_time'])
    
    for idx, exam in exams_df.iterrows():
        exam_date = exam['exam_date']
        start_time = exam['start_time']
        end_time = exam['end_time']
        subject = str(exam.get('subject', '')).strip()
        level = str(exam.get('level', exam.get('grade', ''))).strip()
        section = str(exam.get('section', '')).strip()
        needed = int(exam.get('invigilators_needed', 1))
        
        # Get eligible teachers
        eligible = get_eligible_teachers(
            teachers_df, subject, exam_date, start_time, end_time, assignments
        )
        
        assigned_count = 0
        for i in range(needed):
            if i < len(eligible):
                teacher = eligible[i]
                assignments.append({
                    'exam_date': exam_date,
                    'start_time': start_time,
                    'end_time': end_time,
                    'subject': subject,
                    'level': level,
                    'section': section,
                    'teacher_name': teacher['teacher_name'],
                    'specialty': teacher['specialty'],
                    'notes': 'تخصص مختلف ✓' if teacher['is_different_specialty'] else 'نفس التخصص'
                })
                assigned_count += 1
            else:
                # Not enough teachers
                warnings_list.append({
                    'exam_date': exam_date,
                    'time': f"{start_time} - {end_time}" if start_time and end_time else 'N/A',
                    'subject': subject,
                    'level_section': f"{level} - {section}",
                    'message': f'⚠️ نقص في المراقبات: مطلوب {needed}، تم تعيين {assigned_count} فقط'
                })
    
    return assignments, warnings_list


def assignments_to_dataframe(assignments):
    """Convert assignments list to DataFrame for display"""
    if not assignments:
        return pd.DataFrame()
    
    df = pd.DataFrame(assignments)
    
    # Format for display
    df['التاريخ'] = df['exam_date'].dt.strftime('%Y-%m-%d')
    df['الوقت'] = df.apply(
        lambda x: f"{x['start_time'].strftime('%H:%M') if x['start_time'] else ''} - {x['end_time'].strftime('%H:%M') if x['end_time'] else ''}", 
        axis=1
    )
    df['المادة'] = df['subject']
    df['المستوى والشعبة'] = df['level'] + ' - ' + df['section']
    df['اسم المراقبة'] = df['teacher_name']
    df['الملاحظات'] = df['notes']
    
    # Select and reorder columns
    display_df = df[['التاريخ', 'الوقت', 'المادة', 'المستوى والشعبة', 'اسم المراقبة', 'الملاحظات']]
    
    return display_df


def get_statistics(assignments, teachers_df):
    """Calculate distribution statistics"""
    if not assignments:
        return {}
    
    df = pd.DataFrame(assignments)
    
    # Count per teacher
    teacher_counts = df['teacher_name'].value_counts().to_dict()
    
    # Total assignments
    total = len(assignments)
    
    # Different specialty percentage
    different_specialty = len([a for a in assignments if 'تخصص مختلف' in a.get('notes', '')])
    diff_pct = (different_specialty / total * 100) if total > 0 else 0
    
    # Load balance (std deviation)
    loads = list(teacher_counts.values())
    avg_load = sum(loads) / len(loads) if loads else 0
    max_load = max(loads) if loads else 0
    min_load = min(loads) if loads else 0
    
    return {
        'total_assignments': total,
        'different_specialty_pct': diff_pct,
        'avg_load': avg_load,
        'max_load': max_load,
        'min_load': min_load,
        'teacher_counts': teacher_counts
    }

