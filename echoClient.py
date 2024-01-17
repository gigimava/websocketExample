import argparse
import websockets.client
import asyncio
import sys

if __name__=="__main__":
    parser = argparse.ArgumentParser(prog="WebSockets Echo Client")
    parser.add_argument("host")
    parser.add_argument("port", type=int)
    parser.add_argument("messages", nargs="+")
    args = parser.parse_args()

    async def clientRoutine():
        async with websockets.client.connect("ws://{}:{}".format(args.host, args.port)) as sock:
            for msgSend in args.messages:
                print("Sending message:", msgSend)
                sys.stdout.flush()
                await sock.send(msgSend)
                print("Waiting for response...")
                sys.stdout.flush()
                print("Received:", await sock.recv())
                sys.stdout.flush()

    asyncio.run(clientRoutine())
    