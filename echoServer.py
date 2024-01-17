import argparse
import websockets.server
from websockets import ConnectionClosed
import asyncio
import sys

nClient = 0
async def onRequest(sp):
    global nClient
    nClient += 1
    nClientLocal = nClient
    nRequest = 0
    try:
        while True:
            msg = await sp.recv()
            nRequest += 1
            print("Client {} request {}:".format(nClientLocal, nRequest), msg)
            await sp.send(msg)
    except ConnectionClosed:
        print("Client {} closed".format(nClientLocal))

async def serverLoop(host, port, stop):
    server = await websockets.server.serve(onRequest, host=host, port=port)
    await stop
    print("Shutting down...")
    sys.stdout.flush()
    server.close()
    await server.wait_closed()

if __name__=="__main__":
    parser = argparse.ArgumentParser(prog="WebSockets Echo Server")
    parser.add_argument("host")
    parser.add_argument("port", type=int)
    args = parser.parse_args()
    loop = asyncio.new_event_loop()
    stop = asyncio.Future(loop=loop)
    task=loop.create_task(serverLoop(args.host, args.port, stop))
    async def awaitNewLine():
        print("Running server. Press Enter to terminate...")
        await loop.run_in_executor(None, sys.stdin.readline)
        sys.stdout.flush()
        stop.set_result(None)
    loop.create_task(awaitNewLine())
    loop.run_until_complete(task)
    