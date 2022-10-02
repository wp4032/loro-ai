import os       
import openai   # library for GPT3
import webvtt   # library for reading transcript .vtt files
from dotenv import load_dotenv
from transformers import GPT2Tokenizer
import glob

# ASSEMBLY AI & ZOOM
import sys
import time
import requests
import authlib
import urllib.request
from dotenv import load_dotenv
from pathlib import Path
from typing import Optional, Dict, Union, Any
from authlib.jose import jwt
from requests import Response
import http.client
import json


# Loads the API Key from the .env file
env_path = './.env'
load_dotenv(dotenv_path=env_path)


# Sets API_KEY for whole file
openai.api_key = os.getenv("OPENAI_API_KEY")
API_KEY= os.getenv("ZOOM_API_KEY")
API_SECRET= os.getenv("ZOOM_API_SECRET")
ASSEMBLY_AI_TOKEN = os.getenv("ASSEMBLY_AI_TOKEN")


# Transcript Class
class Transcript:
    '''A class that creates an iterable object for the Loro based on .vtt transcript files'''

    # __init__
    # Creates a transcript object that holds the transcript file & array of lines
    def __init__(self, file: str):
        '''Creates a transcript object that holds the transcript file & array of lines
        
        Args:
            file (str): The file path to the transcript .vtt file
        
        Returns: 
            none (sets up transcript object)
        '''

        self.file = file
        self.lines = []


    # printTranscript()
    # Prints each line of the transcript
    def printTranscript(self):
        '''Prints each line of the transcript
        
        Args: 
            self (Transcript)

        Returns: 
            none (prints each line in terminal)
        '''
        vtt = webvtt.read(self.file)
        for line in vtt:
            print(line)


    # readTranscript()
    # Reads each line of transcript and trims it into 
    def readTranscript(self):
        '''Reads each line of transcript and trims it into
        
        Args: 
            self (Transcript)

        Return:
            none (makes an array self.lines)
        '''
        resultText = ""
        vtt = webvtt.read(self.file)
        previous = ""
        
        for line in vtt:
            line = line.text.strip()
            lineSplit = line.split(": ")
            
            if len(lineSplit) == 2:
                name = lineSplit[0]
                text = lineSplit[1]

                if name == previous:
                    resultText += " " + text
                
                else:
                    start = "\n" + name + ": " + text
                    resultText += start

                previous = name
            
            if len(lineSplit) == 1:
                    resultText += " " + text

        self.lines = resultText.split("\n")


# Loro Transcript Class
class LoroTranscript:
    '''A class that processes a Transcript through GPT3 for summarization'''
    
    # __init__
    # Creates a Loro object to be used to summarize
    def __init__(self, transcript: Transcript, model: str) -> None:
        '''Creates a Loro object to be used to summarize the Transcript object.
        
        Args:
            transcript (Transcript): object that has the transcript of conversation
            model (str): specifies model ("a" [Ada], "b" [Babbage], "c" [Curie], "d" [DaVinci]) 
        
        Return:
            none (a Loro object)
        '''
        self.transcript = transcript

        if model not in "abcd":
            raise Exception("Provided model is not in GPT3 (a [Ada], b [Babbage], c [Curie], d [DaVinci])")

        self.model = model
        self.tokens = []
        self.feathers = []


    # tokenCount
    # Takes a transcript and counts the number of GPT3 tokens in the conversation to be processed into feathers   
    def tokenCount(self):
        '''Takes a transcript and counts the number of GPT3 tokens in the conversation to be processed into feathers
        
        Args:
            self (Loro Object)
            
        Return:
            none (self.tokens is created which is an array with number of tokens per message)
        '''
        tokenizer = GPT2Tokenizer.from_pretrained("gpt2")       
        for line in self.transcript.lines:
            count = tokenizer(line)
            if (len(count.attention_mask) != 0):
                self.tokens.append([line, len(count.attention_mask)])


    # generateFeathers
    # Creates GPT3 prompts (aka feathers) from the conversation
    def generateFeathers(self):
        '''Creates GPT3 prompts (aka feathers) from the conversation
        
        Args:
            self (Loro object)

        Return:
            none (self.feathers which is an array of GPT3-ready prompts)
        '''
        startPrompt = "Create a summary agenda of this conversation:\n"
        feather = startPrompt

        sum = len(feather)
        for tokenCount in self.tokens:
            if sum >= 3200:
                self.feathers.append(feather)
                print(feather)
                feather = startPrompt
                sum = len(feather)
            sum += tokenCount[1]
            feather += "\n" + tokenCount[0]


    # trimFeathers
    # Processes and creates summary from GPT3 prompts (aka trim feathers)
    def trimFeathers(self):
        '''Processes and creates summary from GPT3 prompts (aka trim feathers)
        
        Args:
            self (Loro Object)

        Return:
            none (prints summary to terminal)
        '''
        print(len(self.feathers))
        for feather in self.feathers:
            summary = openai.Completion.create(
                model="text-davinci-002",
                prompt=feather,
                temperature=0.5,
                max_tokens=250,
                presence_penalty = -0.5,
                frequency_penalty = 0.5,
                best_of=5    
            )
            print(summary)


# Zoom Class
class Zoom:
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.jwt_token_exp = 518400
        self.jwt_token_algo = "HS256"
        self.jwt_token : bytes = b'a' 
        self.jwt_token_str : str = ""
        self.headers = {}
        self.userID = ""
        self.jsonDict = {}


    def generateJWTToken(self) -> bytes:
        iat = int(time.time())

        jwt_payload: Dict[str, Any] = {
            "aud": None,
            "iss": self.api_key,
            "exp": iat + self.jwt_token_exp,
            "iat": iat
        }

        header: Dict[str, str] = {"alg": self.jwt_token_algo}

        jwt_token: bytes = jwt.encode(header, jwt_payload, self.api_secret)

        self.jwt_token = jwt_token


    def decodeJWTToken(self):
        self.generateJWTToken()
        self.jwt_token_str = self.jwt_token.decode('UTF-8')
        return self.jwt_token_str


    def makeHeader(self):
        self.decodeJWTToken()
        self.headers = {
            'authorization': "Bearer %s" % self.jwt_token_str,
            'content-type': "application/json"
        }


    def getUserID(self):
        self.getJsonResponse("http://api.zoom.us/v2/users")
        self.userID = self.jsonDict['users'][0]['id']
        return self.userID


    def getJsonResponse(self, link : str):
        self.makeHeader()
        userResponse = requests.get(link, headers=self.headers)
        jsonText = userResponse.text
        jsonDict = json.loads(jsonText)
        self.jsonDict = jsonDict
        return jsonDict


    def getMeetingID(self, type: str = 'previous', index: int = -1):
        if self.userID == "":
            raise Exception("ERROR: User ID has not been generated with the Zoom object")
        link = "http://api.zoom.us/v2/users/" + self.userID + "/meetings?type=" + type
        self.getJsonResponse(link)
        if self.jsonDict['meetings'] == []:
            raise Exception("ERROR: No " + type + " meetings")
        meetingID = self.jsonDict['meetings'][index]['id']
        return meetingID


    def getRecording(self, meetingID):
        if self.userID == "":
            raise Exception("ERROR: User ID has not been generated with the Zoom object")
        link = "http://api.zoom.us/v2/meetings/" + str(meetingID) + "/recordings"
        self.getJsonResponse(link)
        if self.jsonDict['code'] == 3301:
            raise Exception("ERROR: No recordings available")
        recording_url = self.jsonDict['recording_files'][0]['download_url']
        authorized_url = recording_url + "?access_token=" + self.jwt_token_str
        return authorized_url


        
        
# print(API_KEY)
# print(API_SECRET)
# zoom = Zoom(API_KEY, API_SECRET)
# print(zoom.getUserID())
# id = zoom.getMeetingID('upcoming', 0)
# print(zoom.getRecording(id))



folder_path = r"/Users/williampan/Documents/ZOOM/*"
file_type = r'/*vtt'

# Finds the latest Zoom Meeting Folder
folders = glob.glob(folder_path)
latest_folder = max(folders, key=os.path.getctime)

# finds the latest Zoom Meeting Audio
transcripts = glob.glob(latest_folder + file_type)
latest_audio = max(transcripts, key=os.path.getctime)












# # TESTING
# trans = Transcript(r'Loro/testTranscript.vtt')
# trans.readTranscript()
# Loro1 = Loro(trans, "d")
# Loro1.tokenCount()

# openai.Model.list()
# Loro1.generateFeathers()