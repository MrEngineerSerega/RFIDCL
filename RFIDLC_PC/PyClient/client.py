import asyncio

SERVER_IP = "localhost"
SERVER_PORT = 8888


async def main(loop):
    reader, writer = await asyncio.open_connection(SERVER_IP, SERVER_PORT,
                                                   loop = loop)

    writer.write(b"hello world\n")

    data = await reader.read(1024)
    print(data)

    writer.close()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    loop.close()
