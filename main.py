import json
import codecs
import os

from conUtils import ConUtils
from context import Context

def main(harFilePath, resType, reqType, width, filter):
    if (width == "auto"):
        width = os.get_terminal_size()[0] - 33

    urlMaxLength = int(int(width) * 0.65)
    waterfallMaxLength = int(int(width) * 0.35)

    if (urlMaxLength > 120):
        waterfallMaxLength += urlMaxLength - 120
        urlMaxLength = 120

    f = codecs.open(harFilePath, "r", "utf-8")
    jsonContent = f.read()
    har = json.loads(jsonContent)
    context = Context(urlMaxLength, waterfallMaxLength)

    ConUtils.clear()
    context.printRequests(har, resType, reqType, filter)
    selectedRequestId = -1

    while (1):
        print("")
        inp = input("CMD >>: ")
        ConUtils.clear()
        print("")

        if (inp == "list" or inp == "l" or inp == ""):
            if (selectedRequestId > 0):
                context.printRequestDetail(selectedRequestId)
                selectedRequestId = -1
            else:
                context.printRequests(har, resType, reqType, filter)
                selectedRequestId = -1
        elif (inp == "cookies" or inp == "c"):
            context.printCookies()
        elif (inp == "headers" or inp == "h"):
            context.printHeaders()
        elif (inp == "request" or inp == "req"):
            context.requestContent()
        elif (inp == "response" or inp == "res"):
            context.responseContent()
        elif (inp == "websocket" or inp == "w"):
            context.websocketContent()
        elif (inp == "crequest" or inp == "creq"):
            context.copyRequestContent()
        elif (inp == "cresponse" or inp == "cres"):
            context.copyResponseContent()
        elif (inp == "cwebsocket" or inp == "cw"):
            context.copyWebsocketContent()
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
            print("     (ce)xit - exit from app")
        else:
            if (inp.isdecimal()):
                context.printRequestDetail(int(inp))
                selectedRequestId = int(inp)
            else:
                if (inp == "n"):
                    context.printNextRequestDetail()
                elif (inp == "p"):
                    context.printPrevRequestDetail()
                else:
                    print("Showing requests that contains <" + inp + "> in url...")
                    context.printRequests(har, resType, reqType, inp)

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

    main(harFilePath=args.s, resType=args.t, reqType=args.r, width=args.w, filter=args.f)