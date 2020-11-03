import asyncio

PORT = 8888


async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    addr = writer.get_extra_info("peername")
    print("Incoming connection from: {}:{}".format(addr[0], addr[1]))

    data = await reader.read(1024)
    print("Received bytes: {}".format(data))

    writer.write(data.upper())
    await writer.drain()

    writer.close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    connection = asyncio.start_server(handler, "localhost", PORT, loop=loop)
    server = loop.run_until_complete(connection)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print("Closing...")
    finally:
        server.close()
        loop.run_until_complete(server.wait_closed())
        loop.close()
