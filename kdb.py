import tornado
import tornado.web
import tornado.websocket
import tornado.escape
import json
import datetime
import random
import string
import sys
import os

import qpython.qconnection
import perspective

class ManagerMixin(object):
    def check_origin(self, origin):
        return True

    def set_default_headers(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')

class KDBHandler(ManagerMixin, tornado.web.RequestHandler):   
    # Query KDB+, get numpy.recarray
    # Create a perspective table
    # Host the table virtually so browsers can use it - returns an ID
    # Tell the client the virtual table's ID, which it will request via 
    # websocket
    def initialize(self, manager, qconn):
        self._qconn = qconn
        self._manager = manager

    def post(self):
        query = self.request.body.decode("utf-8")
        narray = self._qconn(query)
        table = perspective.Table(narray)
        tbl_id = self._manager.host_table(table)
        self.write(tbl_id)

class PerspectiveWebSocket(ManagerMixin, tornado.websocket.WebSocketHandler):
    # These are virtual calls from the browser - pass them through!
    def initialize(self, manager):
        self._session = manager.new_session()

    def on_message(self, message):
        self._session.process(message, self.write_message)

    def on_close(self):
        self._session.close()

def start_server(manager, qconn):
    app = tornado.web.Application([
        (r"/kdb", KDBHandler, {"qconn": qconn, "manager": manager}),
        (r"/perspective", PerspectiveWebSocket, {"manager": manager})
    ])
    BASE_DIR = os.getcwd()
    try:
        port_number = sys.argv[-1]    

        if port_number.isnumeric():
            port_number = int(port_number)
            port_data = {
                'port_number' : port_number,
            }
            with open (BASE_DIR + "\port-data.json", 'w') as fp:
                json.dump(port_data, fp)
        else:
            port_number = 8888
            port_data = {
                'port_number' : port_number,
            }
            with open (BASE_DIR + "\port-data.json", 'w') as fp:
                json.dump(port_data, fp)

    except:
        port_number = 8888
        port_data = {
                'port_number' : port_number,
            }
            with open (BASE_DIR + "\port-data.json", 'w') as fp:
                json.dump(port_data, fp)
        app.listen(port_number)
    print("Listening on http://localhost:" + port_number)
    loop = tornado.ioloop.IOLoop.current()
    loop.start()

if __name__ == "__main__":
    with qpython.qconnection.QConnection("localhost", 5000) as conn:
        manager = perspective.PerspectiveManager()
        start_server(manager = manager, qconn = conn)
   
    
