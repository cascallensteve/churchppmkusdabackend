from io import BytesIO
from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT


def generate_receipt_pdf(transaction, donor_name, donor_email, mpesa_receipt):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=colors.HexColor('#1a73e8'),
        alignment=TA_CENTER,
        spaceAfter=6,
    )

    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#5f6368'),
        alignment=TA_CENTER,
        spaceAfter=20,
    )

    heading_style = ParagraphStyle(
        'Heading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1a73e8'),
        spaceAfter=10,
    )

    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=11,
        leading=16,
    )

    success_style = ParagraphStyle(
        'Success',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#155724'),
        alignment=TA_CENTER,
        spaceAfter=16,
    )

    story = []
    story.append(Paragraph("MKUSD Church Treasury", title_style))
    story.append(Paragraph("Payment Receipt", subtitle_style))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("Payment Successful", success_style))
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("Transaction Details", heading_style))

    data = [
        ["Transaction ID", f"#{transaction.id}"],
        ["Donation Type", transaction.donation_type.name],
        ["Donor Name", donor_name or "N/A"],
        ["Donor Email", donor_email or "N/A"],
        ["Phone Number", transaction.phone_number],
        ["Amount Paid", f"KSh {transaction.amount}"],
        ["M-Pesa Receipt", mpesa_receipt or "Pending"],
        ["Checkout Request ID", transaction.checkout_request_id or "-"],
        ["Payment Date", transaction.updated_at.strftime("%B %d, %Y")],
        ["Payment Time", transaction.updated_at.strftime("%H:%M") + " (UTC)"],
        ["Status", transaction.status],
    ]

    table = Table(data, colWidths=[7*cm, 8*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a73e8')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 1), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#ffffff'), colors.HexColor('#f8f9fa')]),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))

    story.append(table)
    story.append(Spacer(1, 0.8*cm))
    story.append(Paragraph("We appreciate your support. May God bless you abundantly.", normal_style))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph("If you have any questions, please contact the church treasury office.", normal_style))
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph("MKUSD Church Treasury System<br/>This is an automated receipt. Please do not reply to this email.",
                            ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9,
                                           textColor=colors.HexColor('#6c757d'), alignment=TA_CENTER)))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
