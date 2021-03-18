import argparse
import asyncio
import threading
import os, json, time
import mimetypes


async def dispatch(reader, writer):    # wait for a click and then refresh the following data
    getorhead = 0
    get = 0
    range1 = ""
    path = ""
    while True:
        # request receiving and handling
        data = await reader.readline()      # one line at one time, complete request information got with several lines
        print(data)
        if data == b'\r\n' or data == b'':      # will it possible to be empty?  which representation is right???
            break
        msg = data.decode().split(" ")
        if msg[0] == "GET" or msg[0] == "HEAD":    # GET /(or /xxxx) HTTP/1.0\r\n
            getorhead = 1    # judge method type
            if msg[0] == "GET":
                get = 1
            path = msg[1].replace("\r\n", "")
        if msg[0] == 'Range:':     # Range: bytes=0-11\r\n
            range1 = msg[1].replace("\r\n", "").replace("bytes=", "")

    if getorhead == 0:
        writer.writelines([b'HTTP/1.0 405 Method Not Allowed\r\n',
                           b'Connection: close\r\n',
                           b'\r\n'])
    else:
        path = './' + path
        flag1 = False
        flag2 = False
        try:
            flag1 = os.path.isfile(path)
            flag2 = os.path.isdir(path)
        except FileNotFoundError:
            writer.writelines([b'HTTP/1.0 404 Not Found\r\n',
                               b'Connection: close\r\n',
                               b'\r\n'])

        if flag1:  # document
            try:    # for method os.path.getsize()
                mime = ""
                try:
                    mime = mimetypes.guess_type(path)[0]
                except:
                    mime = 'application/octet-stream'
                typeinfo = 'Content-Type:' + mime + '; charset=utf-8\r\n'
                size = os.path.getsize(path)
                a = 0
                b = size - 1
                if range1 != "":
                    range1 = range1.split('-')
                    a = range1[0]
                    b = range1[1]
                    if a == '':
                        a = 0
                    else:
                        a = int(a)
                    if b == '':
                        b = size - 1
                    else:
                        b = int(b)
                length = b - a + 1
                leninfo = 'Content-Length: ' + str(length) + '\r\n'
                rangeinfo = 'Content-Range: bytes ' + str(a) + '-' + str(b) + '/' + str(size) + '\r\n'
                if range1 != "":
                    writer.writelines([b'HTTP/1.0 206 Partial Content\r\n',
                                       bytes(leninfo, encoding='utf8'),
                                       bytes(rangeinfo, encoding='utf8'),
                                       bytes(typeinfo, encoding='utf8'),
                                       b'Connection: close\r\n',
                                       b'\r\n'])
                else:
                    writer.writelines([b'HTTP/1.0 200 OK\r\n',
                                       bytes(leninfo, encoding='utf8'),
                                       bytes(typeinfo, encoding='utf8'),
                                       b'Connection: close\r\n',
                                       b'\r\n'])
                if get == 1:
                    file = open(path, 'rb')
                    writer.write(file.read())
                    file.close()
            except FileNotFoundError:
                writer.writelines([b'HTTP/1.0 404 Not Found\r\n',
                                   b'Connection: close\r\n',
                                   b'\r\n'])

        elif flag2:  # directory
            try:    # for method os.listdir() and os.path.isdir(path)
                allhref = ''
                for filename in os.listdir(path):
                    if os.path.isfile(path + '/' + filename):
                        allhref = allhref + '<a href="' + filename + '">' + filename + '</a><br>'
                    elif os.path.isdir(path + '/' + filename):
                        allhref = allhref + '<a href="' + filename + '/">' + filename + '/</a><br>'
                html = '<html><head><title>Index of .//</title></head><body bgcolor="white"><h1>Index of .//</h1><hr><pre>' + allhref + '</pre> <hr> </body></html>'
                writer.writelines([b'HTTP/1.0 200 OK\r\n',
                                   b'Content-Type:text/html; charset=utf-8\r\n',
                                   b'Connection: close\r\n',
                                   b'\r\n',
                                   bytes(html, encoding='utf8'),
                                   b'\r\n'])
            except FileNotFoundError:
                writer.writelines([b'HTTP/1.0 404 Not Found\r\n',
                                   b'Connection: close\r\n',
                                   b'\r\n'])

        else:
            writer.writelines([b'HTTP/1.0 404 Not Found\r\n',
                               b'Connection: close\r\n',
                               b'\r\n'])

    writer.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Simple Web File Browser')     # get command line arguments
    parser.add_argument('--port', type=int, default=8080,
                        help='an integer for the port of the simple web file browser')
    parser.add_argument('--dir', type=str, default="./",
                        help='The Directory that the browser should display for home page')
    args = parser.parse_args()
    # base_dir = os.path.abspath(args.dir)
    # print(os.listdir(base_dir))
    os.chdir(args.dir)
    loop = asyncio.get_event_loop()
    coro = asyncio.start_server(dispatch, '127.0.0.1', args.port, loop=loop)
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
