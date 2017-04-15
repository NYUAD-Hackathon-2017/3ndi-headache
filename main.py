#!/usr/bin/env python

from __future__ import division
from __future__ import print_function
from six.moves import xrange

import time

import numpy as np

import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web


SILENCE_FRAME_THRESHOLD = 20000
SILENCE_AVR_THRESHOLD = 50
OVERALL_THRESHOLD = 100


buffer = np.array([])

def chunk_sound(bits):
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


class WSHandler(tornado.websocket.WebSocketHandler):
  connections = []
  buffer = np.array([])
  
  def check_origin(self, origin):
    return True
  
  def open(self):
    print("Client connected")
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
        for i in xrange(0, len(chunks), 640):
          self.write_message(chunks[i:i+640].tostring(), binary=True)
          time.sleep(600/16000)
          
  
  def on_close(self):
    # Remove the connection from the list of connections
    self.connections.remove(self)
    print("Client disconnected")


class NCCOHandler(tornado.web.RequestHandler):
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


if __name__ == '__main__':
  print("Starting server in port 3000")
  http_server = tornado.httpserver.HTTPServer(application)
  http_server.listen(3000)
  tornado.ioloop.IOLoop.instance().start()
