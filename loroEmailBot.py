from array import array
import smtplib
import ssl
import os
import openai
from email.message import EmailMessage
from dotenv import load_dotenv
from zoomAPI import Zoom, LoroTranscript, Transcript

env_path = './.env'
load_dotenv(dotenv_path=env_path)

class LoroEmailBot:
  def __init__(self, recievers: dict, meetingName: str,  summary: str) -> None:
    self.emailSender = 'loro.ai.bot@gmail.com'
    EMAIL_PASSWORD = os.getenv("LORO_BOT_PASSWORD")
    print(EMAIL_PASSWORD)
    self.emailPassword = EMAIL_PASSWORD
    self.emailReceivers = recievers
    self.subject = 'Your meeting notes from ' + meetingName
    self.summary = summary


  def writeEmail(self, name: str):
    head = "Dear " + name + ", \n\n Thanks for a great meeting with Loro.ai. Here are your personalized notes from the meeting:\n\n"
    body = self.summary
    end = "\n\nBest,\nLoro AI Bot :)"
    return head + body + end


  def sendEmails(self):
    for key in self.emailReceivers:
      person = key
      email = self.emailReceivers[key]
      text = self.writeEmail(person)

      em = EmailMessage()
      em['From'] = self.emailSender
      em['To'] = email
      em['Subject'] = self.subject
      em.set_content(text)

      context = ssl.create_default_context()

      with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(self.emailSender, self.emailPassword)
        smtp.sendmail(self.emailSender, email, em.as_string())
        print("Sent Email to " + person + "!")



# CODE TO SEND EMAILS:
API_KEY= os.getenv("ZOOM_API_KEY")
API_SECRET= os.getenv("ZOOM_API_SECRET")

senders = {
  "William": "williampan4032@gmail.com",
  "Andy": "azhu529@gmail.com",
  "Rachel": "rachelloh03@gmail.com",
}

zoomMIT = Zoom(API_KEY, API_SECRET)
userId = zoomMIT.getUserID()
meetingId = zoomMIT.getMeetingID('upcoming', 0)
recording = zoomMIT.getRecording(id)
transMIT = Transcript(r'Loro/testTranscript.vtt')
transMIT.readTranscript()
Loro1 = LoroTranscript(transMIT, "d")
Loro1.tokenCount()
openai.Model.list()
summary = Loro1.generateFeathers()

meetingName = "HackMIT <> Loro.ai"

email = LoroEmailBot(recievers=senders, meetingName=meetingName, summary=summary)
email.sendEmails()

