#!/usr/bin/env python

from __future__ import print_function

import tornado.httpserver
import tornado.websocket
import tornado.ioloop
import tornado.web


class WSHandler(tornado.websocket.WebSocketHandler):
  connections = []
  
  def check_origin(self, origin):
    return True
  
  def open(self):
    print("Client connected")
    # Add the connection to the list of connections
    self.connections.append(self)
  
  def on_message(self, message):
    # Check if message is binary or text
    if type(message) == str:
      print(type(message), len(message))
      # Echo the binary message back to where it came from
      self.write_message(message, binary=True)
    else:
      print("Message received: ", message)
      self.write_message("Your message: " + message)
  
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
