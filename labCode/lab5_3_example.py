import dnslib, time, random
from socket import *

cache = {}

serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('', 10020))
dns = socket(AF_INET, SOCK_DGRAM)

root = [('a.root-servers.net', '198.41.0.4'),
        ('b.root-servers.net', '199.9.14.201'),
        ('c.root-servers.net', '192.33.4.12'),
        ('d.root-servers.net', '199.7.91.13'),
        ('e.root-servers.net', '192.203.230.10'),
        ('f.root-servers.net', '192.5.5.241'),
        ('g.root-servers.net', '192.112.36.4'),
        ('h.root-servers.net', '198.97.190.53'),
        ('i.root-servers.net', '192.36.148.17'),
        ('j.root-servers.net', '192.58.128.30'),
        ('k.root-servers.net', '193.0.14.129'),
        ('l.root-servers.net', '199.7.83.42'),
        ('m.root-servers.net', '202.12.27.33')]

rootDNSCounter = 0
def getRoot():
    global rootDNSCounter
    rootDNSCounter = (rootDNSCounter+1)%12
    return root[rootDNSCounter][1]


# a class of record
class Record():
    currentTime = 0
    ttl = 2e9
    header = None
    rr = None
    auth = None
    ar = None
    def __init__(self, currentTime=0, ttl=2e9, header=None, rr=None, auth=None, ar=None):
        self.currentTime = currentTime
        self.ttl = ttl
        self.header = header
        self.rr = rr
        self.auth = auth
        self.ar = ar


#judge whether {qname, qtype} is in cache
def inCache( qname, qtype ):
    if( qname not in cache ):
        cache[qname] = {}
    if( qtype not in cache[qname] ):
        return False

    currentTime = int(time.time())
    #judge whether time limited exceeded
    if( currentTime - cache[qname][qtype].currentTime >= cache[qname][qtype].ttl ):
        return False
    return True


#get data from cache
def getFromCache( qname, qtype, header ):
    record:Record = cache[qname][qtype]

    currentTime = int(time.time())
    deltaTime = currentTime - record.currentTime

    for rr in record.rr:
        rr.ttl -= deltaTime

    record.currentTime = currentTime
    record.ttl -= deltaTime

    result = dnslib.DNSRecord(dnslib.DNSHeader(id=header.id, qr=header.qr, aa=0, ra=0), q=dnslib.DNSQuestion(qname, qtype), rr=record.rr)
    result.header.qr = 1
    return bytes(result.pack())


#write record into cache
def writeCache( qname, qtype, message ):
    dnsRecord = dnslib.DNSRecord.parse(message)

    ttl = 2e9
    for rr in dnsRecord.rr:
        ttl = min(ttl, rr.ttl)

    record: Record = Record(int(time.time()), ttl, dnsRecord.header, dnsRecord.rr, dnsRecord.a, dnsRecord.ar)

    cache[qname][qtype] = record


def Query( message, address, r, RRs ):
    print(1)
    print(dnslib.DNSRecord.parse(message))
    dns.sendto(message, (address, 53))
    retMessage = dns.recv(2048)

    req = dnslib.DNSRecord.parse(retMessage)
    print(req)
    req.header.rd = 0
    retMessage = bytes(req.pack())
    # print(address)
    # print(req)

    # query from auth's path, get that address then query again.
    if( req.header.a == 0 and req.header.ar == 1 and req.header.auth != 0 ):
        temReq = dnslib.DNSRecord.parse(message)
        temReq.q.qname = dnslib.DNSLabel(str(req.auth[0].rdata))
        temMessage = bytes(temReq.pack())
        temMessage = Query(temMessage, getRoot(), r, RRs )
        temReq = dnslib.DNSRecord.parse(temMessage)
        nextAddress = str(temReq.rr[0].rdata)
        return Query(message, nextAddress, r, RRs )

    #get the answer
    if req.header.a != 0:
        #we get the answer but in CNAME type
        if req.header.a == 1 and req.rr[0].rtype == 5 and r.q.qtype == 1:
            temReq = dnslib.DNSRecord.parse(message)
            temReq.q.qname = dnslib.DNSLabel(str(req.rr[0].rdata))
            message = bytes(temReq.pack())
            RRs.append(req.rr[0])
            return Query(message, getRoot(), r, RRs )
        temReq = dnslib.DNSRecord.parse(retMessage)
        RRs.extend(temReq.rr)
        temReq.rr = RRs
        temReq.header.a = len(RRs)
        return bytes(temReq.pack())
    nextAddress = str(req.ar[0].rdata)
    return Query(message, nextAddress, r, RRs )


if __name__ == '__main__':
    while True:
        message, clientAddress = serverSocket.recvfrom(2048)
        req = dnslib.DNSRecord.parse(message)
        print(message)
        print(req)
        print('Query [%s, %s, %s]'%(clientAddress, req.q.qname, req.q.qtype))
        if( inCache(req.q.qname, req.q.qtype) ):
            #cache read
            print('Get from cache')
            dnsMessage = getFromCache(req.q.qname, req.q.qtype, req.header)
        else:
            print('Get from iterative query')
            temMessage = Query(message, getRoot(), req, [] )
            writeCache(req.q.qname, req.q.qtype, temMessage)
            dnsMessage = getFromCache(req.q.qname, req.q.qtype, req.header)
        print(dnslib.DNSRecord.parse(dnsMessage))

        serverSocket.sendto(dnsMessage, clientAddress)