import pyperclip
from conUtils import ConUtils, fgColors
from harResTypes import replaceResType
import humanize
from prettytable import PrettyTable
import json
from datetime import datetime, timedelta

class Context:
    def __init__(self, har, conWidth: int):
        self.entries = har["log"]["entries"]
        self.lastEntry = {}
        self.lastShowedIds = []
        self.truncateContent = 500
        self.defaultStaticTableWidth = 7
        self.calculateScreenWidthLimits(conWidth)

    def calculateScreenWidthLimits(self, maxScreenWidth):
        maxScreenWidth -= self.calculateMaxTableWidth()

        self.urlMaxLength = int(int(maxScreenWidth) * 0.65)
        self.waterfallMaxLength = int(int(maxScreenWidth) * 0.35)

        if (self.urlMaxLength > 120):
            self.waterfallMaxLength += self.urlMaxLength - 120
            self.urlMaxLength = 120
        
        maxUrlWidth = self.calculateMaxTableUrlWidth()
        totalWidth = maxUrlWidth + self.waterfallMaxLength
        emptySpace = maxScreenWidth - totalWidth

        if (emptySpace > 0):
            emptySpace = maxScreenWidth - totalWidth
            diff = 120 - maxUrlWidth
            if (diff > emptySpace - 1):
                diff = emptySpace - 1

            self.waterfallMaxLength += diff

    def calculateMaxTableWidth(self):
        maxIdWidth = len(str(len(self.entries)))

        maxEntry = max(self.entries, key=lambda x: len(x["request"]["method"]))
        maxRequestTypeWidth = len(maxEntry["request"]["method"])

        maxEntry = max(self.entries, key=lambda x: len(str(x["time"])))
        maxTimeWidth = len(str(maxEntry["time"]))

        return maxIdWidth + maxRequestTypeWidth + maxTimeWidth + self.defaultStaticTableWidth
    
    def calculateMaxTableUrlWidth(self):
        maxUrlLen = 0
        hosts = []
        for id, e in enumerate(self.entries):
            url = e["request"]["url"]
            host = ConUtils.copyHostFromUrl(url)

            if (host != ""):
                if (host not in hosts):
                    hostPlaceholder = "{" + str(len(hosts) + 1) + "}"
                    hosts.append(str(host))
                else:
                    hostPlaceholder = "{" + str(hosts.index(host) + 1) + "}"
                url = ConUtils.replaceHostInUrl(url, host, hostPlaceholder)

            url = ConUtils.shorten(url, self.urlMaxLength)

            if (maxUrlLen < len(url)):
                maxUrlLen = len(url)

        print("max url found = " + str(maxUrlLen))
        return maxUrlLen

    def makeWaterfall(self, startTime, completeTime, timings):
        step = completeTime / self.waterfallMaxLength

        if (step == 0):
            step = 1

        blocked = timings["blocked"]
        send = timings["send"]
        wait = timings["wait"]
        recieve = timings["receive"]

        startSteps = int(startTime / step)
        blockedSteps = int(blocked / step)
        sendSteps = int(send / step)
        waitSteps = int(wait / step)
        recieveSteps = int(recieve / step)

        totalSteps = blockedSteps + sendSteps + waitSteps + recieveSteps

        if (totalSteps == 0):
            recieveSteps = 1

        return " " * startSteps + "—" * blockedSteps + "↑" * sendSteps + "#" * waitSteps + "↓" * recieveSteps

    def isHasBody(self, request):
        method = request["method"]
        if ((method == "POST" or method == "PUT" or method == "DELETE") and request["bodySize"] > 0):
            return True
        return False

    def printCookies(self):
        if (self.lastEntry == {}):
            print("No cookie content available")
            return

        print(" ")
        print(fgColors.YELLOW + "REQUEST —————> Cookies: " + fgColors.ENDC)
        print(ConUtils.prettyContent(self.lastEntry["request"]["cookies"]))
        print(" ")
        print(fgColors.YELLOW + "RESPONSE <————— Cookies: " + fgColors.ENDC)
        print(ConUtils.prettyContent(self.lastEntry["response"]["cookies"]))

    def printHeaders(self):
        if (self.lastEntry == {}):
            print("No header content available")
            return

        print(" ")
        print(fgColors.YELLOW + "REQUEST —————> Headers: " + fgColors.ENDC)
        print(json.dumps(self.lastEntry["request"]["headers"], indent = 4))
        print(" ")
        print(fgColors.YELLOW + "RESPONSE <————— Headers: "+ fgColors.ENDC)
        print(json.dumps(self.lastEntry["response"]["headers"], indent = 4))

    def printNextRequestDetail(self):
        if (self.lastEntry == {}):
            print("No next request available")
            return
        
        id = self.entries.index(self.lastEntry)
        nextId = self.lastShowedIds.index(id) + 1

        if (nextId >= len(self.lastShowedIds)):
            print("No next request available")
            return

        self.printRequestDetail(self.lastShowedIds[nextId])
    
    def printPrevRequestDetail(self):
        if (self.lastEntry == {}):
            print("No next request available")
            return
        
        id = self.entries.index(self.lastEntry)
        nextId = self.lastShowedIds.index(id) - 1
        
        if (nextId < 0):
            print("No previous request available")
            return

        self.printRequestDetail(self.lastShowedIds[nextId])

    def printRequestDetail(self, id):
        if (id < 0 or id >= len(self.entries)):
            print("Invalid request id")
            return
        
        e = self.entries[id]
        self.lastEntry = e
        req = e["request"]
        res = e["response"]

        status: int = e["response"]["status"]
        method = req["method"]

        statusCodeText = ConUtils.colorizeStatusCode(status)
        urlText = ConUtils.colorizeUrlByResourceType(req["url"], e["_resourceType"])

        print("[" + str(id) + "] ——— " + statusCodeText + " " + method + " " + urlText)
        print("")

        startTime = 0
        endTime = startTime + int(e["time"])
        if ("_fromCache" in e):
            print("Cached: " + e["_fromCache"])
        print("Timestamp: " + e["startedDateTime"])
        print("Timing: "+ self.makeWaterfall(startTime, endTime, e["timings"]) +
            " (" + str(int(e["time"])) +" ms)")
        if (int(e["timings"]["_blocked_queueing"]) > 0):
            print("    queued  ( ): " + str(int(e["timings"]["_blocked_queueing"])) + " ms")
        if (int(e["timings"]["blocked"]) > 0):
            print("    blocked (-): " + str(int(e["timings"]["blocked"])) + " ms")
        if (int(e["timings"]["dns"]) > 0):
            print("    dns    : " + str(int(e["timings"]["dns"])) + " ms")
        if (int(e["timings"]["ssl"]) > 0):
            print("    ssl    : " + str(int(e["timings"]["ssl"])) + " ms")
        if (int(e["timings"]["connect"]) > 0):
            print("    connect    : " + str(int(e["timings"]["connect"])) + " ms")
        print("    send    (↑): " + str(int(e["timings"]["send"])) + " ms")
        print("    wait    (#): " + str(int(e["timings"]["wait"])) + " ms")
        print("    receive (↓): " + str(int(e["timings"]["receive"])) + " ms")
        print("")
        if (self.isHasBody(req)):
            print(ConUtils.colorizeText("REQUEST —————> " + req["postData"]["mimeType"] + ": ", fgColors.YELLOW))
        else:
            print(ConUtils.colorizeText("REQUEST —————> " + e["_resourceType"] + " :", fgColors.YELLOW))
        print("    Cookies count: " + str(len(req["cookies"])))
        print("    Headers count: " + str(len(req["headers"])))
        print("    Headers size: " + humanize.naturalsize(req["headersSize"]))
        print("    Body size: " + humanize.naturalsize(req["bodySize"]))
        print("")
        print("Content:")
        if (self.isHasBody(req)):
            if (req["postData"]["mimeType"] == "application/json"):
                print(ConUtils.shorten(ConUtils.prettyContent(req["postData"]["text"]), self.truncateContent))
            else:
                print(ConUtils.shorten(ConUtils.prettyContent(req["postData"]["params"]), self.truncateContent))
        else:
            print(ConUtils.shorten(ConUtils.prettyContent(req["queryString"]), self.truncateContent))

        print("")
        print(ConUtils.colorizeText("RESPONSE <————— " + res["content"]["mimeType"] +":", fgColors.YELLOW))
        print("    Status: " + ConUtils.colorizeStatusCode(status))
        if (status != 0):
            print("    Cookies count: " + str(len(res["cookies"])))
            print("    Headers count: " + str(len(res["headers"])))
            print("    Headers size: " + humanize.naturalsize(res["headersSize"]))
            print("    Body size: " + humanize.naturalsize(res["content"]["size"]))
            print("")
            print("Content:")
            if (len(res["redirectURL"]) > 0):
                print("    Redirected: " + res["redirectURL"])
            if (res["content"]["size"] > 0):
                if (res["content"]["mimeType"] != "application/json"):
                    print(ConUtils.shorten(ConUtils.prettyContent(res["content"]["text"]), self.truncateContent))
                else:
                    print(ConUtils.shorten(ConUtils.prettyContent(res["content"]["text"]), self.truncateContent))
        else:
            print("    Error: " + res["_error"])

        if (e["_resourceType"] == "websocket"):
            print("")
            print(ConUtils.colorizeText("WEBSOCKET:", fgColors.YELLOW))
            print(ConUtils.shorten(ConUtils.prettyContent(e["_webSocketMessages"]), self.truncateContent))

    def printRequests(self, resType, reqType, filter):
        initTime = datetime.fromisoformat(self.entries[0]["startedDateTime"])
        latestEntry = max(self.entries, key=lambda x: int(ConUtils.timeToMs(datetime.fromisoformat(x["startedDateTime"]) - initTime)
            + x["time"]))

        completeTime = int(ConUtils.timeToMs(datetime.fromisoformat(latestEntry["startedDateTime"]) - initTime)
            + latestEntry["time"])

        hosts = []
        hostPlaceholder = "{" + str(len(hosts) + 1) + "}"

        self.lastShowedIds = []
        t = PrettyTable(['Id', 'Req', 'Res', 'Url', "Time", "Waterfall"])
        t.align = "l"
        for id, e in enumerate(self.entries):
            startTime = ConUtils.timeToMs(datetime.fromisoformat(e["startedDateTime"]) - initTime)
            url = e["request"]["url"]
            host = ConUtils.copyHostFromUrl(url)

            if (host != ""):
                if (host not in hosts):
                    hostPlaceholder = "{" + str(len(hosts) + 1) + "}"
                    hosts.append(str(host))
                else:
                    hostPlaceholder = "{" + str(hosts.index(host) + 1) + "}"
                url = ConUtils.replaceHostInUrl(url, host, hostPlaceholder)

            urlShorten = ConUtils.shorten(url, self.urlMaxLength)
            urlShorten = ConUtils.colorizeUrlByResourceType(urlShorten, e["_resourceType"],)

            time = ConUtils.colorizeExecutionTime(int(e["time"]), "_fromCache" in e)
            statusCode = ConUtils.colorizeStatusCode(int(e["response"]["status"]))

            if ((resType == "all" or replaceResType(e["_resourceType"]) == resType) and
                (reqType == "all" or e["request"]["method"].lower() == reqType) and
                (filter == "" or (filter.lower() in url.lower()))):
                t.add_row([id, e["request"]["method"], statusCode,
                    urlShorten, time,
                    self.makeWaterfall(startTime, completeTime, e["timings"])])
                self.lastShowedIds.append(id)
        print(t)

        for id, host in enumerate(hosts):
            print("{" + str(id + 1) + "} = " + host)

        completeTimeHumanized = humanize.naturaldelta(timedelta(microseconds=completeTime * 1000))
        print("Total recorded time: " + str(completeTimeHumanized) + " (" + str(completeTime) + " ms)")

    def copyRequestContent(self):
        if (self.lastEntry == {}):
            print("No request content available")

        method = self.lastEntry["request"]["method"]
        if ((method == "POST" or method == "PUT" or method == "DELETE") and self.lastEntry["request"]["bodySize"] > 0):
            if (self.lastEntry["request"]["postData"]["mimeType"] == "application/json"):
                pyperclip.copy(ConUtils.prettyContent(self.lastEntry["request"]["postData"]["text"]))
            else:
                pyperclip.copy(ConUtils.prettyContent(self.lastEntry["request"]["postData"]["params"]))
            print("Request content copyied to clipboard")
        else:
            pyperclip.copy(ConUtils.prettyContent(self.lastEntry["request"]["queryString"]))

    def copyResponseContent(self):
        if (self.lastEntry != {} and self.lastEntry["response"]["content"]["size"] > 0):
            text = ConUtils.prettyContent(self.lastEntry["response"]["content"]["text"])
            pyperclip.copy(text)
            print("Response content copyied to clipboard")
        else:
            print("No response content available")

    def copyWebsocketContent(self):
        if (self.lastEntry != {} and self.lastEntry["_resourceType"] == "websocket"):
            print("WebSocket content copyied to clipboard")
            pyperclip.copy(ConUtils.prettyContent(self.lastEntry["_webSocketMessages"]))
        else:
            print("No WebSocket content available")

    def requestContent(self):
        if (self.lastEntry == {}):
            print("No request content available")

        res = ""
        print("Request content:")

        method = self.lastEntry["request"]["method"]
        if ((method == "POST" or method == "PUT" or method == "DELETE") and self.lastEntry["request"]["bodySize"] > 0):
            if (self.lastEntry["request"]["postData"]["mimeType"] == "application/json"):
                res = ConUtils.prettyContent(self.lastEntry["request"]["postData"]["text"])
            else:
                res = ConUtils.prettyContent(self.lastEntry["request"]["postData"]["params"])
            print(res)
        else:
            print(ConUtils.prettyContent(self.lastEntry["request"]["queryString"]))

    def responseContent(self):
        if (self.lastEntry != {} and self.lastEntry["response"]["content"]["size"] > 0):
            res = ConUtils.prettyContent(self.lastEntry["response"]["content"]["text"])
            print("Response content:")
            print(res)
        else:
            print("No response content available")

    def websocketContent(self):
        if (self.lastEntry != {} and self.lastEntry["_resourceType"] == "websocket"):
            print("Websocket content:")
            print(ConUtils.prettyContent(self.lastEntry["_webSocketMessages"]))
        else:
            print("No WebSocket content available")