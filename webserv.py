import socket
import sys
import time
import re
import os
import zlib
import gzip


def getConfig():
    if len(sys.argv)==1:
        print("Missing Configuration Argument")
        sys.exit()
    try:
        with open (sys.argv[1]) as fcon:
            pass
    except:
        print("Unable To Load Configuration File")
        sys.exit()

    try:
        with open (sys.argv[1]) as fcon:
            line=fcon.readline()
            if "staticfiles" in line:
                statFile=line.split("=",1)[1].rsplit()[0]
            else:
                raise ValueError
            line=fcon.readline()
            if "cgibin" in line:
                cgiBin=line.split("=",1)[1].rsplit()[0]
            else:
                raise ValueError
            line=fcon.readline()
            if "port" in line:
                port=int(line.split("=",1)[1].rsplit()[0])
            else:
                raise ValueError
            line=fcon.readline()
            if "exec" in line:
                execPath=line.split("=",1)[1].rsplit()[0]
            else:
                raise ValueError
            
    except:
        print("Missing Field From Configuration File")
        sys.exit()

    return statFile,cgiBin,port,execPath

def header(num,fileType,cgiBool):

    if num==200:
        #print("filetype",fileType)
        msg=b"HTTP/1.1 200 OK\n"
        if fileType=="html":
            msg+=b"Content-Type: text/html\n"
        if fileType=="js":
            msg+=b"Content-Type: application/javascript\n"
        elif fileType=="txt":
            msg+=b"Content-Type: text/plain\n"
        elif fileType=="css":
            msg+=b"Content-Type: text/css\n"
        elif fileType=="png":
            msg+=b"Content-Type: image/png\n"
        elif fileType=="jpg" or fileType=="jpeg":
            msg+=b"Content-Type: image/jpeg\n"
        elif fileType=="xml":
            msg+=b"Content-Type: text/xml\n"
        elif fileType=="done":
            pass
    

    elif num==404:
        msg=b"HTTP/1.1 404 File not found\nContent-Type: text/html\n\n"
        msg+=b"""\
<html>
<head>
	<title>404 Not Found</title>
</head>
<body bgcolor="white">
<center>
	<h1>404 Not Found</h1>
</center>
</body>
</html>
"""

    return msg


def request(cliSock):
    request=cliSock.recv(1024).decode()
    if not request: 
        return
    time.sleep(0.1) #remove
    # print(request)

    reqMethod=request.split(' ')[0]
    fileSend=request.split(' ')[1]
    gzipBool="Accept-Encoding: gzip" in request #if we have to gzip or not
    # print(gzipBool)
    if reqMethod=="GET":
        if not(fileSend.startswith("/cgibin")): #return Static file
            if fileSend=="/":
                fileSend="/index.html"

            fileSend=statFile+fileSend
            # print("file to printout:",fileSend)
            try:
                with open(str(fileSend),'rb') as f:
                    fileType=fileSend.split('.')[2]
                    head=header(200,fileType,False)
                    #print(head)
                    fileCont=f.read()
                    if gzipBool:
                        try:
                            fileCont=gzip.compress(fileCont)
                        except:
                            pass
                        # print(fileCont)
                        head+=b"Content-Encoding: gzip\n"

                    msg=head+b"\n"+fileCont
                    if reqMethod=="HEAD":
                        msg=head.rstrip(b"\n")+b"\n"
                    
                    # print(msg.decode()) #see output before sending
                    cliSock.sendall(msg)
                    
            except Exception as e:
                msg=header(404,'error',False)
                # print(e)
                cliSock.sendall(msg)
                pass

        elif fileSend.startswith("/cgibin"): #return the cgi program's output
            fileExe=re.search('/cgibin(.*)?', fileSend)
            fileExe=cgiBin+(fileExe.group(1).split("?",1)[0])

            rfd,wfd=os.pipe()

            #set up the env var
            newEnv=dict(os.environ)
            newEnv["REQUEST_METHOD"]="GET"
            newEnv["HTTP_USER_AGENT"]=" " or re.search('User-Agent:\s(.*)\n', request).group(1)
            newEnv["HTTP_ACCEPT"]=" " or re.search('Accept:\s(.*)\n', request).group(1)
            newEnv["SERVER_ADDR"]=str(serSock.getsockname()[0])
            newEnv["SERVER_PORT"]=str(serSock.getsockname()[1])
            newEnv["REMOTE_ADDRESS"]=str(cliSock.getsockname()[0])
            newEnv["REMOTE_PORT"]=str(cliSock.getsockname()[1])
            newEnv["REQUEST_URI"]=fileSend.split("?",1)[0]
            if "?" in fileSend:
                newEnv["QUERY_STRING"]=fileSend.split("?",1)[1]
            else:
                newEnv["QUERY_STRING"]=""


            pid = os.fork()   
            if pid==0:      #child executes the cgi
                try:
                    os.dup2(wfd,1)
                    # os.execlpe(fileExe,"serverProg",os.environ)
                    os.execve(execPath,[execPath,fileExe],newEnv)

                except Exception as e:  #500 Internal Server Error cgi error
                    cliSock.sendall(str(e).encode())
                    sys.exit(1)

            elif pid == -1:     #error when forking       
                sys.exit(1)

            elif pid>0:           #parent continues  

                wval = os.wait()
                
                if(wval[1]>>8 != 0):
                    cliSock.sendall(b'HTTP/1.1 500 Internal Server Error\n')
                    # cgi failed  500 Internal Server Error
                else:
                    cgiBody= os.read(rfd,1024)
                    
                    # print(header(200,"html",True))
                    if b"Content-Type:" in cgiBody:
                        head=header(200,"done",True)
                        if b"Status-Code:" in cgiBody:
                            head=head.lstrip(b"HTTP/1.1 200 OK")
                            statCode=re.search(b'Status-Code:\s(.*)\n', cgiBody).group(1) #get status code from cgiBody
                            head=b"HTTP/1.1 "+ statCode
                            cgiBody=cgiBody.lstrip(b"Status-Code:"+statCode) #remove the line from response
                        if gzipBool:
                            try:
                                cgiBody=gzip.compress(cgiBody)
                            except Exception as e:
                                pass
                        msg=head+cgiBody
                            
                        # cliSock.sendall(msg)
                    else:
                        head=header(200,"html",True)    #default html if no content type given
                        if b"Status-Code:" in cgiBody:
                            head=head.lstrip(b"HTTP/1.1 200 OK")
                            statCode=re.search(b'Status-Code:\s(.*)\n', cgiBody).group(1)
                            head=b"HTTP/1.1 "+ statCode 
                            cgiBody= cgiBody.lstrip(b"Status-Code:"+statCode)
                        if gzipBool:
                            try:
                                cgiBody=gzip.compress(cgiBody)

                            except Exception as e:
                                pass
                        msg=head+b"\n"+cgiBody
                        # print(msg)
                        # print(cgiBody)

                    cliSock.sendall(msg)

                    # print(msg)
                    


def createServer():
    global serSock
    serSock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    serSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        serSock.bind(('127.0.0.1',port))
        serSock.listen(5)
        while True:
            cliSock,addr=serSock.accept()
            request(cliSock)
            #print("Connection from", addr)
            # cliSend="HTTP/1.1 200 OK\nContent-Type: text/html\n\n<h1>Welcome to my home page</h1>\n"
            # cliSock.send(cliSend.encode())
            cliSock.close()

    except Exception as e :
        cliSock.sendall(str(e).encode())
        serSock.close()

#*************************************************************************************************************************************************************

global statFile,cgiBin,port,execPath,serSock
statFile,cgiBin,port,execPath=getConfig()
createServer()
# print(statFile,cgiBin,port,execPath)

#yaayy!
# def setEnv(request,cliSock):
#     newEnv=dict(os.environ)
#     newEnv["REQUEST_METHOD"]=request.split(' ')[0]
#     newEnv["HTTP_USER_AGENT"]=" " or re.search('User-Agent:\s(.*)\n', request).group(1) 
#     newEnv["HTTP_ACCEPT"]=" " or re.search('Accept:\s(.*)\n', request).group(1)
#     newEnv["HTTP_ACCEPT_ENCODING"]=" " or re.search('Accept-Encoding:\s(.*)\n', request).group(1)
#     newEnv["REMOTE_ADDRESS"]=cliSock.getsockname()[0]
#     newEnv["REMOTE_PORT"]=cliSock.getsockname()[1]
#     newEnv["SERVER_ADDR"]=serSock.getsockname()[0]
#     newEnv["SERVER_PORT"]=serSock.getsockname()[1]
#     newEnv["QUERY_STRING"]=" " or request.split('\n')[0].split("?",1)[1]
#     return newEnv
