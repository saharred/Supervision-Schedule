"""
PDF Export for Supervision Schedule
Matches the official template format
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from datetime import datetime
import io


def export_to_pdf_v2(daily_schedule, school_name="مدرسة عثمان بن عفان النموذجية للبنين",
                     academic_year="2025-2026", level_name="", semester="الفصل الدراسي الأول"):
    """
    Export daily schedule to PDF matching the template
    
    Args:
        daily_schedule: dict with date, day_name, and exams list
        school_name: name of the school
        academic_year: academic year
        level_name: level/grade name
        semester: semester name
    
    Returns:
        BytesIO buffer with PDF document
    """
    buffer = io.BytesIO()
    
    # Create PDF
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # Register Arabic font
    try:
        pdfmetrics.registerFont(TTFont('Arabic', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
        arabic_font = 'Arabic'
    except:
        arabic_font = 'Helvetica'
    
    # Styles
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'ArabicTitle',
        parent=styles['Heading1'],
        fontName=arabic_font,
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=10,
        leading=20
    )
    
    subtitle_style = ParagraphStyle(
        'ArabicSubtitle',
        parent=styles['Normal'],
        fontName=arabic_font,
        fontSize=13,
        alignment=TA_CENTER,
        spaceAfter=8,
        leading=18
    )
    
    normal_style = ParagraphStyle(
        'ArabicNormal',
        parent=styles['Normal'],
        fontName=arabic_font,
        fontSize=11,
        alignment=TA_CENTER,
        leading=14
    )
    
    small_style = ParagraphStyle(
        'ArabicSmall',
        parent=styles['Normal'],
        fontName=arabic_font,
        fontSize=9,
        alignment=TA_CENTER,
        leading=12
    )
    
    # Build content
    content = []
    
    # Header table (school name, year, ministry)
    header_data = [
        [
            Paragraph('وزارة التربية والتعليم والتعليم العالي<br/>Ministry of Education and Higher Education', small_style),
            Paragraph(f'<b>العام الأكاديمي {academic_year}</b>', normal_style),
            Paragraph(f'<b>{school_name}</b><br/>Othman bin Affan school for boys', normal_style)
        ]
    ]
    
    header_table = Table(header_data, colWidths=[6*cm, 5*cm, 6*cm])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), arabic_font),
    ]))
    
    content.append(header_table)
    content.append(Spacer(1, 0.5*cm))
    
    # Title box
    title_data = [
        [Paragraph('<b>جدول مراقبة الورقة الأولى لاختبارات</b>', title_style)],
        [Paragraph(f'<b>منتصف {semester}</b>', subtitle_style)],
        [Paragraph(f'<b>الورقة الأولى ({level_name})</b>', normal_style)]
    ]
    
    title_table = Table(title_data, colWidths=[17*cm])
    title_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), arabic_font),
    ]))
    
    content.append(title_table)
    content.append(Spacer(1, 0.5*cm))
    
    # Date and subject info
    date_str = daily_schedule['date'].strftime('%Y-%m-%d')
    day_name = daily_schedule['day_name']
    
    # Get unique subjects and grades
    subjects = set([exam['subject'] for exam in daily_schedule['exams']])
    subjects_str = ' - '.join(subjects)
    
    grades = set([exam['grade'] for exam in daily_schedule['exams']])
    grades_str = ' و '.join(grades)
    
    info_data = [
        [Paragraph(f'<b>اليوم: {day_name}</b>', normal_style), Paragraph(f'<b>التاريخ: {date_str}</b>', normal_style)],
        [Paragraph(f'<b>المادة: {subjects_str}</b>', normal_style), Paragraph(f'<b>الصف: {grades_str}</b>', normal_style)]
    ]
    
    info_table = Table(info_data, colWidths=[8.5*cm, 8.5*cm])
    info_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#D9D9D9')),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, -1), arabic_font),
    ]))
    
    content.append(info_table)
    content.append(Spacer(1, 0.5*cm))
    
    # Main schedule table
    # Group exams by subject
    exams_by_subject = {}
    for exam in daily_schedule['exams']:
        subject = exam['subject']
        if subject not in exams_by_subject:
            exams_by_subject[subject] = []
        exams_by_subject[subject].append(exam)
    
    # Build table data
    table_data = []
    
    # Header row
    table_data.append([
        Paragraph('<b>التوقيع</b>', normal_style),
        Paragraph('<b>المراقب الثاني</b>', normal_style),
        Paragraph('<b>التوقيع</b>', normal_style),
        Paragraph('<b>المراقب الأول</b>', normal_style),
        Paragraph('<b>الصف</b>', normal_style),
        Paragraph('<b>المادة</b>', normal_style)
    ])
    
    # Data rows
    for subject, exams in exams_by_subject.items():
        for idx, exam in enumerate(exams):
            row = [
                '',  # Signature
                Paragraph(exam['supervisor2'], normal_style),
                '',  # Signature
                Paragraph(exam['supervisor1'], normal_style),
                Paragraph(f"{exam['grade']} {exam['section']}", normal_style),
                Paragraph(f'<b>{subject}</b>', normal_style) if idx == 0 else ''
            ]
            table_data.append(row)
    
    # Reserve row
    table_data.append([
        Paragraph('<b>الاحتياط</b>', normal_style),
        '', '', '', '', ''
    ])
    
    # Create table
    schedule_table = Table(table_data, colWidths=[2.5*cm, 3*cm, 2.5*cm, 3*cm, 3*cm, 3*cm])
    
    # Calculate row spans for subjects
    style_commands = [
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), arabic_font),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.black),
        # Header row styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8B0000')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        # Reserve row styling
        ('BACKGROUND', (0, len(table_data)-1), (-1, len(table_data)-1), colors.HexColor('#8B0000')),
        ('TEXTCOLOR', (0, len(table_data)-1), (-1, len(table_data)-1), colors.whitesmoke),
        ('SPAN', (0, len(table_data)-1), (-1, len(table_data)-1)),
    ]
    
    # Add subject column styling (light pink background)
    current_row = 1
    for subject, exams in exams_by_subject.items():
        num_rows = len(exams)
        if num_rows > 1:
            style_commands.append(('SPAN', (5, current_row), (5, current_row + num_rows - 1)))
        style_commands.append(('BACKGROUND', (5, current_row), (5, current_row + num_rows - 1), colors.HexColor('#FFC7CE')))
        current_row += num_rows
    
    schedule_table.setStyle(TableStyle(style_commands))
    
    content.append(schedule_table)
    content.append(Spacer(1, 0.8*cm))
    
    # Footer with signatures
    footer_data = [
        [
            Paragraph('النائب الأكاديمي: مريم القصع', normal_style),
            Paragraph('النائب الإداري: دلال الفهيدة', normal_style)
        ]
    ]
    
    footer_table = Table(footer_data, colWidths=[8.5*cm, 8.5*cm])
    footer_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), arabic_font),
    ]))
    
    content.append(footer_table)
    content.append(Spacer(1, 0.3*cm))
    
    # School principal
    content.append(Paragraph('<b>مديرة المدرسة: منيرة الهاجري</b>', normal_style))
    content.append(Spacer(1, 0.3*cm))
    
    # Motto
    motto_style = ParagraphStyle(
        'Motto',
        parent=styles['Normal'],
        fontName=arabic_font,
        fontSize=9,
        alignment=TA_CENTER,
        textColor=colors.grey
    )
    content.append(Paragraph('<i>رؤيتنا: مجتمع رياضي لتنمية مستدامة</i>', motto_style))
    
    # Build PDF
    doc.build(content)
    
    # Save to file
    import tempfile
    import os
    
    # Create temp file
    fd, temp_path = tempfile.mkstemp(suffix='.pdf')
    os.close(fd)
    
    # Write buffer to file
    buffer.seek(0)
    with open(temp_path, 'wb') as f:
        f.write(buffer.getvalue())
    
    return temp_path

