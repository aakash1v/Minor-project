import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SENDER_EMAIL = "examplenamez543@gmail.com"
SENDER_PASSWORD = "mfnppwcnqlmpzymc"

def send_email(subject, recipient_email, body):
    try:
        # Setup MIME
        message = MIMEMultipart()
        message['From'] = SENDER_EMAIL
        message['To'] = recipient_email
        message['Subject'] = subject

        message.attach(MIMEText(body, 'plain'))

        # Create SMTP session for sending the mail
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(message)
        server.quit()

        print(f"Email sent to {recipient_email}")
    except Exception as e:
        print(f"Error sending email: {e}")


def send_approval_email(recipient_email, student_name, leave_reason):
    subject = "Leave Request Approved"
    body = f"Dear {student_name},\n\nYour leave request for the reason '{leave_reason}' has been approved.\n\nBest regards,\nAdmin"
    send_email(subject, recipient_email, body)


def send_rejection_email(recipient_email, student_name, leave_reason):
    subject = "Leave Request Rejected"
    body = f"Dear {student_name},\n\nYour leave request for the reason '{leave_reason}' has been rejected.\n\nBest regards,\nAdmin"
    send_email(subject, recipient_email, body)

def send_contact_email(sender_name, sender_email, message_text):
    subject = f"New Contact Form Submission from {sender_name}"
    body = f"""
    You have received a new contact form submission:

    Name: {sender_name}
    Email: {sender_email}
    Message:
    {message_text}
    """
    send_email(subject, "aakashkumarpy@gmail.com", body)

def send_otp(sender_name, recipient_email, otp):
    subject = f"Hello {sender_name} , otp : {otp}"
    body = f"Dear {sender_name}, \n\nYour otp is {otp}"
    send_email(subject, recipient_email, body)