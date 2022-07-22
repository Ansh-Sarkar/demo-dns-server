import glob
import json


def LOAD_ZONES():
    jsonZone = {}
    zoneFiles = glob.glob('zones/*.zone')
    
    for zone in zoneFiles:
        with open(zone, 'r') as zoneData:
            print("Zone Data : ", zoneData)
            try:
                data = json.load(zoneData)
            except Exception as error:
                print(error)
            zoneName = data["$origin"]
            jsonZone[zoneName] = data
            
    return jsonZone

ZONE_DATA = LOAD_ZONES()

def bytePrint(byteString):
    for byte in byteString:
        print(hex(byte), end=' ')
    print("\n")
    
def getFlags(flagData):
    
    byte1 = bytes(flagData[0])
    byte2 = bytes(flagData[1])
    
    responseFlags = ''
    
    # parsing first byte
    QR = '1'
    
    OPCODE = ''
    for bit in range(1, 5):
        OPCODE += str(ord(byte1)&(1<<bit))
        
    AA = '1'
    TC = '0'
    RD = '0'
    
    # parsing second byte
    RA = '0'
    Z = '000'
    RCODE = '0000'
    
    return int(QR + OPCODE + AA + TC + RD, 2).to_bytes(1, byteorder='big') + int(RA + Z + RCODE, 2).to_bytes(1, byteorder='big') 

def getQuestionDomain(questionDomainData):
    
    state, counter, expectedLength, domainString, domainParts, qDOMEnd = 0, 0, 0, '', [], 0
    
    for byte in questionDomainData:
        if state == 1:
            if byte:
                domainString += chr(byte)
            counter += 1
            if counter == expectedLength:
                domainParts.append(domainString)
                domainString, counter, state = '', 0, 0
            if not byte:
                domainParts.append(domainString)
                break
        else:
            state = 1
            expectedLength = byte
        qDOMEnd += 1
    
    questionType = questionDomainData[qDOMEnd : qDOMEnd + 2]
    print("questionType :", questionType)
    
    return (domainParts, questionType)

def getZone(domainData):
    global ZONE_DATA
    
    zoneName = '.'.join(domainData)
    return ZONE_DATA[zoneName]

def getRecs(data):
    domain, questionType = getQuestionDomain(data)
    qt = ''
    
    if questionType == b'\x00\x01':
        qt = 'a'
        
    zone = getZone(domain)
    return (zone[qt], qt, domain)

def buildQuestion(domainName, recType):
    qBytes = b''
    
    for part in domainName:
        length = len(part)
        qBytes += bytes([length])
        
        for char in part:
            qBytes += ord(char).to_bytes(1, byteorder='big')

    if recType == 'a':
        qBytes += (1).to_bytes(2, byteorder='big')
        
    qBytes += (1).to_bytes(2, byteorder='big')
    
    return qBytes

def recToBytes(domainName, recType, recTTL, recValue):
    rBytes = b'\xc0\x0c'
    
    if recType == 'a':
        rBytes = rBytes + bytes([0]) + bytes([1])
        
    rBytes = rBytes + bytes([0]) + bytes([1])
    
    rBytes += int(recTTL).to_bytes(4, byteorder='big')
    
    if recType == 'a':
        rBytes = rBytes + bytes([0]) + bytes([4])
        
        print("recValue :", recValue)
        for part in recValue.split('.'):
            rBytes += bytes([int(part)])
            
    return rBytes

def buildResponse(data):
    
    # get transaction ID (1st and 2nd byte)
    transactionID = data[:2]
    tid = ''
    
    bytePrint(transactionID)
    for byte in transactionID:
        tid += hex(byte)[2:]
    print("TID :", tid)
    
    # get flags (3rd and 4th byte)
    flags = getFlags(data[2:4])
    print("flags :", flags)
    
    # setting question count
    QDCOUNT = b'\x00\x01'
    
    # setting answer count
    ANCOUNT = len(getRecs(data[12:])[0]).to_bytes(2, byteorder='big')
    
    # nameserver count
    NSCOUNT = (0).to_bytes(2, byteorder='big')
    
    # additional count
    ARCOUNT = (0).to_bytes(2, byteorder='big')
    
    DNSHeader = transactionID + flags + QDCOUNT + ANCOUNT + NSCOUNT + ARCOUNT
    print("DNS Header :", DNSHeader)
    
    DNSBody = b''
    records, recType, domainName = getRecs(data[12:])
    print("DNS Body :", DNSBody)
    
    DNSQuestion = buildQuestion(domainName, recType)
    print("DNS Question :", DNSQuestion)
    
    for record in records:
        print("record :", records)
        DNSBody += recToBytes(domainName, recType, record["ttl"], record["value"])
        
    return DNSHeader + DNSQuestion + DNSBody