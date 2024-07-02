import json
import codecs
import os

from context import Context

def main(harFilePath, resType, reqType, width):
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

    context.printRequests(har, resType, reqType)

    while (1):
        print("")
        inp = input("CMD >>: ")
        print("")

        if (inp == "list" or inp == "l" or inp == ""):
            context.printRequests(har, resType, reqType)
        elif (inp == "cookies" or inp == "c"):
            context.printCookies()
        elif (inp == "headers" or inp == "h"):
            context.printHeaders()
        elif (inp == "request" or inp == "req"):
            context.copyRequestContent()
        elif (inp == "response" or inp == "res"):
            context.copyResponseContent()
        elif (inp == "websocket" or inp == "w"):
            context.copyWebsocketContent()
        elif (inp == "exit" or inp == "e"):
            exit(0)
        elif (inp == "help" or inp == "!help" or inp == "!h"):
            print("This is a CMD help:")
            print("     <Id> - print request details with certain Id from table above")
            print("     <EMPTY> or (l)ist - print all requests")
            print("     (c)ookie - print cookies for latest selected request")
            print("     (req)uest - copy to clipboard request content from latest selected request")
            print("     (res)ponse -  copy to clipboard response content from latest selected request")
            print("     (w)ebsocket - copy to clipboard websocket content from latest selected request")
            print("     (e)xit - exit from app")
        else:
            if (inp.isdecimal()):
                context.printRequestDetail(int(inp))
            else:
                print("Invalid request id")

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Create a HarView scheme')
    parser.add_argument('-s', metavar='Path', required=True, help='Path to har file')
    parser.add_argument('-f', metavar='Resource filter', required=False, 
                        help='Filter requests by resource type (doc, js, css, etc ...)', default="all")
    parser.add_argument('-t', metavar='Type filter', required=False, 
                        help='Filter requests by type (GET, POST, etc ...)', default="all")
    parser.add_argument('-w', metavar='Max screen width', required=False, 
                        help='Set display width in units (default is auto)', default="auto")
    args = parser.parse_args()

    main(harFilePath=args.s, resType=args.f, reqType=args.t, width=args.w)