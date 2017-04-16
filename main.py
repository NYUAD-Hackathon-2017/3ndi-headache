#!/usr/bin/env python

from __future__ import division
from __future__ import print_function
from six.moves import xrange

import json
import requests
import time
import uuid

import numpy as np

import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web

import secrets


###############################################################################
### Audio preprocessing-- chunking for words and phrases/sentences          ###
###############################################################################

# Threshold parameters

SILENCE_FRAME_THRESHOLD = 12000
SILENCE_AVR_THRESHOLD = 50
OVERALL_THRESHOLD = 100


buffer = np.array([])

def chunk_sound(bits):
  """Accumulate sounds from input stream until enough silence is detected."""
  global buffer
  buffer = np.append(buffer, bits)
  abs_buffer = np.absolute(buffer)
  # Keep accumulating if not enough silence has been detected
  if len(buffer) <= SILENCE_FRAME_THRESHOLD:
    return np.array([])
  # If enough silence, clear the buffer
  last_timespan = abs_buffer[-SILENCE_FRAME_THRESHOLD:]
  if np.average(last_timespan) < SILENCE_AVR_THRESHOLD:
    # If there is enough sound, return it
    if np.average(abs_buffer) >= OVERALL_THRESHOLD:
      result = buffer
      buffer = np.array([])
      return result
    buffer = np.array([])
  return np.array([])


###############################################################################
### Speech recognition and synthesis using Nuance API                       ###
###############################################################################

SR_URL = "https://dictation.nuancemobility.net:443/NMDPAsrCmdServlet/dictation"
TTS_URL = "https://tts.nuancemobility.net:443/NMDPTTSCmdServlet/tts"

LANG_CODES = {
  'arabic': 'ara-XWW',
  'english': 'eng-USA',
}

PARAMS = {
  'arabic': {
    'appId': secrets.appId_arabic,
    'appKey': secrets.appKey_arabic,
    'id': uuid.uuid4(),
    'voice': 'Laila',
  },
  'english': {
    'appId': secrets.appId_english,
    'appKey': secrets.appKey_english,
    'id': uuid.uuid4(),
    'voice': 'Zoe',
  },
}

def speech_to_text(audio, languages=None):
  headers = {
    'Content-Type': 'audio/x-wav;codec=pcm;bit=16;rate=16000',
    'Accept': 'text/plain;charset=utf-8',
    'Accept-Topic': 'Dictation',
    'X-Dictation-NBestListSize': '1',
  }
  results = []
  if not languages:
    languages = ('english', 'arabic')
  for language in languages:
    headers.update({
      'Accept-Language': LANG_CODES[language],
      'Content-Length': len(audio),
    })
    r = requests.post(SR_URL,
      params=PARAMS[language], headers=headers, data=audio)
    # TODO: return an empty string if the server returned an error
    results.append(r.text)
  return results

def text_to_speech(text, language='english'):
  headers = {
    'Content-Type': 'text/plain;charset=utf-8',
    'Accept': 'audio/x-wav;codec=pcm;bit=16;rate=16000',
  }
  r = requests.post(TTS_URL,
    params=PARAMS[language], headers=headers, data=text)
  return r.content


###############################################################################
### Web application                                                         ###
###############################################################################

PLAY_TTS_URL = "https://api.nexmo.com/v1/calls/{}/stream"
conversation_uuid = None
payload = {
  'stream_url': ['http://nyuadhack2017.ngrok.io/static/test.wav']
}


class WSHandler(tornado.websocket.WebSocketHandler):
  """Handler for the phone call web socket."""
  connections = []
  
  def check_origin(self, origin):
    return True
  
  def open(self):
    # Add the connection to the list of connections
    self.connections.append(self)
  
  def on_message(self, message):
    # Check if message is binary or text
    if type(message) == str:
      # Read little-endian encoded sound
      bits = np.fromstring(message, dtype='<i2')
      # Chunk the read bits
      chunks = chunk_sound(bits).astype('<i2')
      if len(chunks) > 0:
        # Echo the binary message back to where it came from
        recording = chunks.tostring()
        ### TODO: add support for Arabic if there is time
        print("Sending STT request")
        text_input = speech_to_text(recording, languages=['english'])[0]
        print(text_input)
        
        ### TODO: all the NLP here
        text_response = text_input
        
        print("Sending TTS request")
        speech_response = text_to_speech(text_response, 'english')
        for i in xrange(0, len(speech_response), 640):
          self.write_message(speech_response[i:i+640], binary=True)
          time.sleep(320/16000)
  
  def on_close(self):
    # Remove the connection from the list of connections
    self.connections.remove(self)


class NCCOHandler(tornado.web.RequestHandler):
  """Main handler that instructs Nuance to connect to the web socket."""
  
  def get(self):
    with open('ncco.json', 'r') as f:
      ncco = f.read()
    self.write(ncco)
    self.set_header('Content-Type', 'application/json')
    self.finish()
  
  def post(self):
    print('POST:', self.request.body)
    global conversation_uuid
    conversation_uuid = json.loads(self.request.body)['uuid']
    self.finish()


# Router
application = tornado.web.Application([
  (r'/socket', WSHandler),
  (r'/', NCCOHandler),
])

if __name__ == '__main__':
  # Tornado
  print("Starting server in port 3000")
  http_server = tornado.httpserver.HTTPServer(application)
  http_server.listen(3000)
  tornado.ioloop.IOLoop.instance().start()
