from io import BytesIO
import os
from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT


LOGO_PATH = os.path.join(settings.BASE_DIR, 'payments', 'static', 'payments', 'images', 'logo.png')


def generate_receipt_pdf(transaction, donor_name, donor_email, mpesa_receipt):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#111827'),
        alignment=TA_CENTER,
        spaceAfter=4,
    )

    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#6b7280'),
        alignment=TA_CENTER,
        spaceAfter=18,
    )

    label_style = ParagraphStyle(
        'Label',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#6b7280'),
        fontName='Helvetica-Bold',
        spaceAfter=2,
    )

    value_style = ParagraphStyle(
        'Value',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#111827'),
        fontName='Helvetica-Bold',
        alignment=TA_LEFT,
        spaceAfter=2,
    )

    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=11,
        leading=16,
        textColor=colors.HexColor('#374151'),
    )

    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#9CA3AF'),
        alignment=TA_CENTER,
    )

    story = []

    if os.path.exists(LOGO_PATH):
        logo = Image(LOGO_PATH, width=1.8*cm, height=1.8*cm)
        logo.hAlign = 'CENTER'
        story.append(logo)
        story.append(Spacer(1, 0.4*cm))

    story.append(Paragraph("MKUSDA Church", title_style))
    story.append(Paragraph("Mount Kenya University, Thika | MKUSDA Church Treasury System", subtitle_style))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("Payment Successful", ParagraphStyle(
        'Success',
        parent=styles['Normal'],
        fontSize=13,
        textColor=colors.HexColor('#065F46'),
        alignment=TA_CENTER,
        spaceAfter=14,
    )))

    data = [
        ["Receipt Number", f"#{transaction.id}"],
        ["Date", transaction.updated_at.strftime("%B %d, %Y")],
        ["Member Name", donor_name or "N/A"],
        ["Email Address", donor_email or "N/A"],
        ["Phone Number", transaction.phone_number],
        ["Donation Type", transaction.donation_type.name],
        ["Payment Method", "M-Pesa"],
    ]

    if transaction.transaction_desc:
        data.append(["Notes / Remarks", transaction.transaction_desc])

    table = Table(data, colWidths=[5.5*cm, 9*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ffffff')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#111827')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 1), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ffffff')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#ffffff'), colors.HexColor('#f9fafb')]),
        ('LEFTPADDING', (0, 0), (-1, -1), 14),
        ('RIGHTPADDING', (0, 0), (-1, -1), 14),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))

    story.append(table)
    story.append(Spacer(1, 0.6*cm))

    amount_table = Table(
        [["Amount Paid", f"KSh {transaction.amount}"]],
        colWidths=[7*cm, 7.5*cm]
    )
    amount_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#5B21B6')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
        ('LEFTPADDING', (0, 0), (-1, -1), 20),
        ('RIGHTPADDING', (0, 0), (-1, -1), 20),
    ]))
    story.append(amount_table)
    story.append(Spacer(1, 0.8*cm))

    story.append(Paragraph("Thank you for your generous giving", ParagraphStyle(
        'Thanks',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#374151'),
        alignment=TA_CENTER,
        spaceAfter=4,
    )))
    story.append(Paragraph("If you have any questions, please contact the church treasury office.", footer_style))
    story.append(Spacer(1, 0.8*cm))
    story.append(Paragraph("MKUSDA Church Treasury System", footer_style))
    story.append(Paragraph(f"&copy; {transaction.updated_at.strftime('%Y')} MKUSDA Church. All rights reserved.", footer_style))
    story.append(Paragraph("This is an automated receipt. Please do not reply to this email.", footer_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
