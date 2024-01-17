import argparse
import websockets.server
import websockets.client
from websockets import ConnectionClosed
import asyncio
import sys

async def serverLoop(host, port, stop, queueClient):
    nClient = 0
    async def onRequest(sp):
        nonlocal nClient
        nClient += 1
        nClientLocal = nClient
        queue = asyncio.Queue(1)
        nRequest = 0
        try:
            while True:
                msgRequest = await sp.recv()
                print("Client {} request {}:".format(nClientLocal, nRequest), msgRequest)
                await queueClient.put((queue, msgRequest))
                msgResponse = await queue.get()
                print("Client {} response {}:".format(nClientLocal, nRequest), msgResponse)
                await sp.send(msgResponse)
        except ConnectionClosed:
            print("Client {} closed".format(nClientLocal))

    server = await websockets.server.serve(onRequest, host=host, port=port)
    await stop
    print("Shutting down...")
    sys.stdout.flush()
    server.close()
    await server.wait_closed()

async def clientLoop(host, port, stop, queue):
    dictActiveRequests = {}
    async with websockets.client.connect("ws://{}:{}".format(host, port)) as sock:
        async def fetchFromQueue():
            while not stop.done():
                (queueResult, msg) = await queue.get()
                print("Sending message:", msg)
                dictActiveRequests[msg] = queueResult
                await sock.send(msg)

        async def fetchFromSocket():
            while not stop.done():
                msg = await sock.recv()
                print("Received:", msg)
                dictActiveRequests[msg].put_nowait(msg)
                del dictActiveRequests[msg]

        await asyncio.gather(fetchFromQueue(), fetchFromSocket())

if __name__=="__main__":
    parser = argparse.ArgumentParser(prog="WebSockets Relay Server")
    parser.add_argument("hostListen")
    parser.add_argument("portListen", type=int)
    parser.add_argument("hostServer")
    parser.add_argument("portServer", type=int)
    args = parser.parse_args()
    loop = asyncio.new_event_loop()
    stop = asyncio.Future(loop=loop)
    queue = asyncio.Queue()
    taskServer=loop.create_task(serverLoop(args.hostListen, args.portListen, stop, queue))
    taskClient=loop.create_task(clientLoop(args.hostServer, args.portServer, stop, queue))
    async def awaitNewLine():
        print("Running server. Press Enter to terminate...")
        await loop.run_in_executor(None, sys.stdin.readline)
        sys.stdout.flush()
        stop.set_result(None)
    loop.create_task(awaitNewLine())
    loop.run_until_complete(asyncio.gather(taskClient, taskServer))
    