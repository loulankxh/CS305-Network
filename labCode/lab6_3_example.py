import os, asyncio, mimetypes, argparse


class Header:
    def __init__(self):
        self.method = ''
        self.path = ''
        self.host = ''
        self.range = ''


def raiseError( writer, code ):
    if code == 405:
        print('[405Error] Method Not Allowed.')
        writer.writelines([b'HTTP/1.0 405 Method Not Allowed\r\n', b'Connection: close\r\n', b'405\r\n', b'\r\n'])
    elif code == 404:
        print('[404Error] Not found.')
        writer.writelines([b'HTTP/1.0 404 Not Found\r\n', b'Connection: close\r\n', b'405\r\n', b'\r\n'])


def getType(path):
    try:
        mime = mimetypes.types_map[os.path.splitext(path)[1]]
        print(mime)
        print(mimetypes.guess_type(path)[0])
    except:
        mime = 'application/octet-stream'
    return mime


def getHtml(path):
    list = os.listdir(path)
    hefs = '<a href="../">../</a><br>'
    for element in list:
        if os.path.isdir( path+'/'+element ):
            element = element + '/'
        hefs = hefs + '<a href="{}">{}</a><br>'.format(element,element)
    result = '<html><head><title>Index of .//</title></head> <body bgcolor="white"> <h1>Index of .//</h1><hr> <pre>{}</pre> <hr> </body></html>'.format(hefs)
    return result


async def dispatch(reader, writer):
    header = Header()
    print("start111111111111")
    while True:
        data = await reader.readline()
        print(1)
        print(data)
        message = data.decode().split(' ')
        print(2)
        print(message)
        if data == b'\r\n' or data == b'':
            break
        if message[0] == 'GET' or message[0] == 'HEAD':
            header.method = message[0].split('\r\n')[0]
            header.path = message[1].split('\r\n')[0]
        if message[0] == 'Host:':
            header.host = message[1].split('\r\n')[0]
        if message[0] == 'Range:':
            header.range = message[1].split('\r\n')[0].strip('bytes=')

    if header.method == '':
        raiseError(writer, 405)
    else:
        path = './' + header.path
        if os.path.isdir(path):
            html = getHtml(path)
            writer.writelines([b'HTTP/1.0 200 OK\r\n',
                               b'Content-Type:text/html; charset=utf-8\r\n',
                               b'Connection: close\r\n',
                               b'\r\n',
                               bytes(html, encoding='utf8'),
                               b'\r\n'])
        elif os.path.isfile(path):
            try:
                len = os.path.getsize(path)
                start = 0
                end = len-1
                type = getType(path)
                response = 'HTTP/1.0 200 OK\r\n'
                if header.range != '':
                    start, end = header.range.split('-')
                    if( start == '' and end == '' ):
                        start = 0
                        end = len-1
                    elif( end == '' ):
                        start = int(start)
                        end = len-1
                    elif( start == '' ):
                        end = int(end)
                        start = 0
                    else:
                        start = int(start)
                        end = int(end)
                    response = response + 'Content-Range: bytes {}-{}/{}\r\n'.format(start, end, len)
                response = response + 'Content-Type: {}; charset=utf-8\r\nContent-Length: {}; Connection: close\r\n\r\n'.format(type, end-start+1)
                writer.write(bytes(response, encoding='utf8'))
                if header.method == 'GET':
                    file = open(path, 'rb')
                    content = file.read(len)
                    writer.write(content)
                    file.close()
            except FileNotFoundError:
                raiseError(writer, 404)
        else:
            raiseError(writer, 404)

    await writer.drain()
    writer.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Simple Web File Browser')
    parser.add_argument('--port', type=int, default=8080, help='an integer for the port of the simple web file browser')
    parser.add_argument('--dir', type=str, default="./",
                        help='The Directory that the browser should display for home page')
    args = parser.parse_args()
    print("server run at port %d" % args.port)
    print("server run at dir %s" % args.dir)
    loop = asyncio.get_event_loop()
    coro = asyncio.start_server(dispatch, '127.0.0.1', args.port, loop=loop)
    os.chdir(args.dir)
    server = loop.run_until_complete(coro)
    # Serve requests until Ctrl+C is pressed
    print('Serving on {}'.format(server.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    # Close the server
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()