import json
import codecs
import os

from conUtils import ConUtils
from context import Context

def inputCMD():
    print("")
    inp = input("CMD >>: ")
    ConUtils.clear()
    print("")

    return inp

def main(harFilePath, resType, reqType, conWidth, filter):
    if (conWidth == "auto"):
        conWidth = os.get_terminal_size()[0]

    f = codecs.open(harFilePath, "r", "utf-8")
    jsonContent = f.read()
    har = json.loads(jsonContent)
    context = Context(har, conWidth)

    ConUtils.clear()
    context.printRequests(resType, reqType, filter)

    selectedRequestId = -1
    isNeedRestoreRequestDetails = True
    while (1):
        inp = inputCMD()

        if (inp == "list" or inp == "l" or inp == ""):
            if (selectedRequestId >= 0 and isNeedRestoreRequestDetails):
                context.printRequestDetail(selectedRequestId)
                isNeedRestoreRequestDetails = False
            else:
                selectedRequestId = -1
                context.printRequests(resType, reqType, filter)
        elif (inp == "exit" or inp == "e"):
            exit(0)
        elif (inp == "help" or inp == "!help" or inp == "!h"):
            print("This is a CMD help:")
            print("     <Id> - print request details with certain Id from table above")
            print("     <EMPTY> or <SEARCH PATTERN> - print all requests or request that contains <SEARCH PATTERN> in url")
            print("     (c)ookie - print cookies for latest selected request")
            print("     (req)uest - prin request content from latest selected request")
            print("     (res)ponse -  print response content from latest selected request")
            print("     (w)ebsocket - print websocket content from latest selected request")
            print("     (creq)uest - copy to clipboard request content from latest selected request")
            print("     (cres)ponse -  copy to clipboard response content from latest selected request")
            print("     (cw)ebsocket - copy to clipboard websocket content from latest selected request")
            print("     (e)xit - exit from app")
        elif (inp == "n"):
            selectedRequestId += 1
            context.printNextRequestDetail()
        elif (inp == "p"):
            selectedRequestId -= 1
            context.printPrevRequestDetail()
        elif (inp == "cookies" or inp == "c"):
            isNeedRestoreRequestDetails = True
            context.printCookies()
        elif (inp == "headers" or inp == "h"):
            isNeedRestoreRequestDetails = True
            context.printHeaders()
        elif (inp == "request" or inp == "req"):
            isNeedRestoreRequestDetails = True
            context.requestContent()
        elif (inp == "response" or inp == "res"):
            isNeedRestoreRequestDetails = True
            context.responseContent()
        elif (inp == "websocket" or inp == "w"):
            isNeedRestoreRequestDetails = True
            context.websocketContent()
        elif (inp == "crequest" or inp == "creq"):
            isNeedRestoreRequestDetails = True
            context.copyRequestContent()
        elif (inp == "cresponse" or inp == "cres"):
            isNeedRestoreRequestDetails = True
            context.copyResponseContent()
        elif (inp == "cwebsocket" or inp == "cw"):
            isNeedRestoreRequestDetails = True
            context.copyWebsocketContent()
        else:
            if (inp.isdecimal()):
                selectedRequestId = int(inp)
                context.printRequestDetail(int(inp))
            else:
                print("Showing requests that contains <" + inp + "> in url...")
                context.printRequests(resType, reqType, inp)

                
               

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Create a HarView scheme')
    parser.add_argument('-s', metavar='Path', required=True, help='Path to har file')
    parser.add_argument('-t', metavar='Request by resource type filter', required=False, 
                        help='Filter requests by resource type (doc, js, css, etc ...)', default="all")
    parser.add_argument('-r', metavar='Request type filter', required=False, 
                        help='Filter requests by type (GET, POST, etc ...)', default="all")
    parser.add_argument('-w', metavar='Max screen width', required=False, 
                        help='Set display width in units (default is auto)', default="auto")
    parser.add_argument('-f', metavar='Max screen width', required=False, 
                        help='Set display width in units (default is auto)', default="")
    args = parser.parse_args()

    main(harFilePath=args.s, resType=args.t, reqType=args.r, conWidth=args.w, filter=args.f)