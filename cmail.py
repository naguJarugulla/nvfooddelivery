import smtplib
from smtplib import SMTP
from email.message import EmailMessage
def sendmail(to,subject,body):
    server=smtplib.SMTP_SSL('smtp.gmail.com',465)
    server.login('nagalakshmijarugulla2003@gmail.com ','xjfdvctsxvsnaorm')
    msg=EmailMessage()
    msg['From']='nagalakshmijarugulla2003@gmail.com'
    msg['Subject']=subject
    msg['To']=to
    msg.set_content(body)
    server.send_message(msg)
    server.quit()
