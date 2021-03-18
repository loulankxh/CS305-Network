import dnslib
from socket import *

port = 12000
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('0.0.0.0', port))
print("the server is ready to receive")

# this is the list for root servers
list_rootdns = [("b.root-servers.net.", "199.9.14.201"),
                ("c.root-servers.net.", "192.33.4.12"),
                ("k.root-servers.net.", "193.0.14.129"),
                ("i.root-servers.net.", "192.36.148.17"),
                ("l.root-servers.net.", "199.7.83.42"),
                ("h.root-servers.net.", "198.97.190.53"),
                ("f.root-servers.net.", "192.5.5.241"),
                ("g.root-servers.net.", "192.112.36.4"),
                ("m.root-servers.net.", "202.12.27.33"),
                ("e.root-servers.net.", "192.203.230.10"),
                ("a.root-servers.net.", "198.41.0.4"),
                ("d.root-servers.net.", "199.7.91.13"),
                ("j.root-servers.net.", "192.58.128.30")]
cache = {}


def query(msg, cname_ans, ip):     # cname_ans: answer record for cname type
    info = dnslib.DNSRecord.parse(msg)
    info.header.rd = 0     # set rd 0
    msg = bytes(info.pack())
    serverSocket.sendto(msg, (ip, 53))
    receive = serverSocket.recv(2048)
    receive = dnslib.DNSRecord.parse(receive)
    print(3)
    print(receive)

    if receive.header.a == 0:   # find no answer
        if receive.header.ar > 1:    # except OPT information
            newip = str(receive.ar[0].rdata)
            return query(msg, cname_ans, newip)
        nameserver = receive.auth[0].rdata
        newmsg = dnslib.DNSRecord.question(str(nameserver), "A")
        newmsg = dnslib.DNSRecord.parse(newmsg)
        newmsg = bytes(newmsg.pack())     # type: # from DNSRecord to bytes
        newinfo = query(newmsg, cname_ans, list_rootdns[0][1])
        newip = str(newinfo.rr[0].rdata)    # for name server, there is not cname record in answer
        return query(msg, cname_ans, newip)
    else:    # find answers
        if receive.rr[0].rtype == 5:    # type == CNAME   ??? rr rr[0] rtype
            newmsg = dnslib.DNSRecord.question(str(receive.rr[0].rdata), "A")
            newmsg = bytes(newmsg.pack())
            cname_ans.append(receive.rr[0])
            return query(newmsg, cname_ans, list_rootdns[0][1])
        else:    # type == A   (1)
            tmp = receive.rr
            receive.rr = cname_ans
            receive.rr.extend(tmp)
            receive.header.a = len(receive.rr)
            receive = bytes(receive.pack())
            return receive


if __name__ == "__main__":
    while True:
        msg, clientAddress = serverSocket.recvfrom(2048)
        print(1)
        print(msg)
        info = dnslib.DNSRecord.parse(msg)
        print(info)
        id = info.header.id
        name = info.q.qname
        # serverSocket.sendto(msg, (list_rootdns[0][1], 53))   # dnslib.DNSRecord.send(info, list_rootdns[0][1])???  serverSocket.send ???
        # rev = serverSocket.recv(2048)    # dnslib.DNSRecord.reply(2048)? ???
        if info.q.qname in cache:   # only consider A type
            ans = cache[info.q.qname]
        else:
            ans = query(msg, [], list_rootdns[0][1])
            ans = dnslib.DNSRecord.parse(ans)
            ans.q.qname = name
            ans = bytes(ans.pack())
            cache[info.q.qname] = ans
        ans = dnslib.DNSRecord.parse(ans)
        ans.header.id = id
        print(ans)
        ans = bytes(ans.pack())

        serverSocket.sendto(ans, clientAddress)



