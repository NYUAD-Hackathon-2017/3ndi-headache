from __future__ import print_function

import tornado.ioloop
import tornado.web
import tornado.websocket


class MainHandler(tornado.web.RequestHandler):
  def get(self):
    self.write("Hello, world")


class EchoWebSocket(tornado.websocket.WebSocketHandler):
  def check_origin(self, origin):
    return True
  
  def open(self):
    print("WebSocket opened")

  def on_message(self, message):
    self.write_message(u'You said: ' + message)
  
  def on_close(self):
    print("WebSocket closed")


def make_app():
  return tornado.web.Application([
    (r'/', MainHandler),
    (r'/socket', EchoWebSocket),
  ])


if __name__ == "__main__":
  print("Starting app in http://localhost:3000")
  app = make_app()
  app.listen(3000)
  tornado.ioloop.IOLoop.current().start()
