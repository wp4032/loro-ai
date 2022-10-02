from array import array
import smtplib
import ssl
import os
from email.message import EmailMessage
from dotenv import load_dotenv

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
    head = "Dear" + name + ", \n\nThanks for a great meeting with Loro.ai. Here are your personalized notes from the meeting:\n\n"
    body = self.summary
    end = """\n\n
    Best,
    Loro AI Bot :)
    """
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


# TEST:

senders = {
  "William": "williampan4032@gmail.com",
  "Rachel": "rachelloh03@gmail.com"
}
summary = "Test Summary"
meetingName = "Test Meeting"
test = LoroEmailBot(recievers=senders, meetingName=meetingName, summary=summary)
print()
test.sendEmails()

