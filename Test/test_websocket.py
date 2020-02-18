from websocket_server import WebsocketServer

def new_client(client, server):
    print ("new_client:", client['address'])

def message_received(client, server, message):
    print ("message_received:", message)
    server.send_message(client, "hello from server")

server = WebsocketServer(port=5001, host='127.0.0.1')
server.set_fn_new_client(new_client)
server.set_fn_message_received(message_received)
server.run_forever()