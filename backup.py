#!/usr/bin/env python

from __future__ import division
from __future__ import print_function
from six.moves import xrange

from multiprocessing import Process, Pipe
import requests
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

WORD_FRAME_THRESHOLD = 1500
SENTENCE_FRAME_THRESHOLD = 12000
SILENCE_AVR_THRESHOLD = 50
OVERALL_THRESHOLD = 100
MIN_LEN = 3000


word_buffer = np.array([])

def chunk_word(bits):
  """Accumulate sounds from input stream until enough silence is detected."""
  global word_buffer
  word_buffer = np.append(word_buffer, bits)
  abs_buffer = np.absolute(word_buffer)
  # Keep accumulating if not enough silence has been detected
  if len(word_buffer) <= WORD_FRAME_THRESHOLD:
    return np.array([])
  # If enough silence, clear the buffer
  last_timespan = abs_buffer[-WORD_FRAME_THRESHOLD:]
  if np.average(last_timespan) < SILENCE_AVR_THRESHOLD:
    # If there is enough sound, return it
    if np.average(abs_buffer) >= OVERALL_THRESHOLD and len(abs_buffer) >= MIN_LEN:
      result = word_buffer
      word_buffer = np.array([])
      return result
    word_buffer = np.array([])
  return np.array([])


sentence_buffer = np.array([])

def chunk_sentence(bits):
  """Accumulate sounds from input stream until enough silence is detected."""
  global sentence_buffer
  sentence_buffer = np.append(sentence_buffer, bits)
  abs_buffer = np.absolute(sentence_buffer)
  # Keep accumulating if not enough silence has been detected
  if len(sentence_buffer) <= SENTENCE_FRAME_THRESHOLD:
    return False
  # If enough silence, clear the buffer
  last_timespan = abs_buffer[-SENTENCE_FRAME_THRESHOLD:]
  if np.average(last_timespan) < SILENCE_AVR_THRESHOLD:
    # If there is enough sound, return it
    if np.average(abs_buffer) >= OVERALL_THRESHOLD:
      result = sentence_buffer
      sentence_buffer = np.array([])
      return True
    sentence_buffer = np.array([])
  return False


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

def speech_to_text(char_connection):
  while True:
    audio = char_connection.recv()
    headers = {
      'Content-Type': 'audio/x-wav;codec=pcm;bit=16;rate=16000',
      'Accept': 'text/plain;charset=utf-8',
      'Accept-Topic': 'Dictation',
      'X-Dictation-NBestListSize': '1',
    }
    results = []
    for language in ('english', 'arabic'):
      headers.update({
        'Accept-Language': LANG_CODES[language],
        'Content-Length': len(audio),
      })
      r = requests.post(asr_url,
        params=PARAMS[language], headers=headers, data=audio).text
      # Return an empty string if the server returned an error
      if r.startswith('<html>'):
        r = ''
      results.append(r.text)
    # TODO: how to send results to method?
    print(results)
    char_connection.send(results)

def text_to_speech(char_connection):
  while True:
    text, language = char_connection.recv()
    headers = {
      'Content-Type': 'text/plain;charset=utf-8',
      'Accept': 'audio/x-wav;codec=pcm;bit=16;rate=16000',
    }
    r = requests.post(TTS_URL,
      params=PARAMS[language], headers=headers, data=text)
    char_connection.send(r.content)


###############################################################################
### Web application                                                         ###
###############################################################################

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
      word_chunks = chunk_word(bits).astype('<i2')
      sentence_chunks = chunk_sentence(bits).astype('<i2')
      if len(word_chunks) > 0:
        # Echo the binary message back to where it came from
        recording = word_chunks.tostring()
        print("Sending request")
        stt_parent.send(recording)
        tts_parent.send(recording)
  
  def on_close(self):
    # Remove the connection from the list of connections
    self.connections.remove(self)


class NCCOHandler(tornado.web.RequestHandler):
  """Main handler that instructs Nuance to connect to the web socket."""
  
  def get(self):
    print('GET:', self.request.body)
    with open('ncco.json', 'r') as f:
      ncco = f.read()
    self.write(ncco)
    self.set_header('Content-Type', 'application/json')
    self.finish()
  
  def post(self):
    print('POST:', self.request.body)
    self.finish()


# Router

application = tornado.web.Application([
  (r'/socket', WSHandler),
  (r'/', NCCOHandler),
])


###############################################################################
### Server startup                                                          ###
###############################################################################

if __name__ == '__main__':
  
  # Create threads for async calls to Nuance
  
  stt_parent, stt_child = Pipe()
  stt_process = Process(target=speech_to_text, args=(stt_child,))
  stt_process.start()
  
  tts_parent, tts_child = Pipe()
  tts_process = Process(target=text_to_speech, args=(tts_child,))
  tts_process.start()
  
  # Start Tornado
  
  print("Starting server in port 3000")
  http_server = tornado.httpserver.HTTPServer(application)
  http_server.listen(3000)
  tornado.ioloop.IOLoop.instance().start()
