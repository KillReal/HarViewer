import pyperclip
from conUtils import ConUtils, fgColors
from harResTypes import replaceResType
import humanize
from prettytable import PrettyTable
import json
from datetime import datetime, timedelta

class HarViewer:
    def __init__(self, har, conWidth: int):
        self.entries = har["log"]["entries"]
        self.selectedEntry = {}
        self.lastShowedIds = []
        self.truncateContent = 500
        self.defaultStaticTableWidth = 22
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

        maxEntry = max(self.entries, key=lambda x: len(str(int(x["time"]))))
        maxTimeWidth = len(str(int(maxEntry["time"])))

        return maxIdWidth + maxRequestTypeWidth + maxTimeWidth + self.defaultStaticTableWidth
    
    def calculateMaxTableUrlWidth(self):
        maxUrlLen = 0
        hosts = []
        for e in self.entries:
            url = e["request"]["url"]
            host = ConUtils.selectHostFromUrl(url)

            if (host != ""):
                if (host not in hosts):
                    hostPlaceholder = "{" + str(len(hosts) + 1) + "}"
                    hosts.append(str(host))
                else:
                    hostPlaceholder = "{" + str(hosts.index(host) + 1) + "}"
                url = ConUtils.replaceHostInUrl(url, host, hostPlaceholder)

            url = ConUtils.shorten(url, self.urlMaxLength)
            urlLen = len(url)

            if (maxUrlLen < urlLen):
                maxUrlLen = urlLen

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
    
    def getResourceType(self, entry):
        resourceType = "unknown"
        request = entry["request"]
        if (self.isHasBody(request)):
            resourceType = request["postData"]["mimeType"]
        elif ("_resourceType" in entry):
            resourceType = entry["_resourceType"]
        return resourceType

    def printCookies(self):
        if (self.selectedEntry == {}):
            print("No cookie content available")
            return

        print(" ")
        print(fgColors.YELLOW + "REQUEST —————> Cookies: " + fgColors.ENDC)
        print(ConUtils.prettyContent(self.selectedEntry["request"]["cookies"]))
        print(" ")
        print(fgColors.YELLOW + "RESPONSE <————— Cookies: " + fgColors.ENDC)
        print(ConUtils.prettyContent(self.selectedEntry["response"]["cookies"]))

    def printHeaders(self):
        if (self.selectedEntry == {}):
            print("No header content available")
            return

        print(" ")
        print(fgColors.YELLOW + "REQUEST —————> Headers: " + fgColors.ENDC)
        print(json.dumps(self.selectedEntry["request"]["headers"], indent = 4))
        print(" ")
        print(fgColors.YELLOW + "RESPONSE <————— Headers: "+ fgColors.ENDC)
        print(json.dumps(self.selectedEntry["response"]["headers"], indent = 4))

    def printNextRequestDetail(self):
        if (self.selectedEntry == {}):
            print("No next request available")
            return
        
        id = self.entries.index(self.selectedEntry)
        nextId = self.lastShowedIds.index(id) + 1

        if (nextId >= len(self.lastShowedIds)):
            print("No next request available")
            return

        self.printRequestDetails(self.lastShowedIds[nextId])
    
    def printPrevRequestDetail(self):
        if (self.selectedEntry == {}):
            print("No next request available")
            return
        
        id = self.entries.index(self.selectedEntry)
        nextId = self.lastShowedIds.index(id) - 1
        
        if (nextId < 0):
            print("No previous request available")
            return

        self.printRequestDetails(self.lastShowedIds[nextId])

    def printRequestDetails(self, id):
        if (id < 0 or id >= len(self.entries)):
            print("Invalid request id")
            return
        
        e = self.entries[id]
        self.selectedEntry = e
        req = e["request"]
        res = e["response"]
        timings = e["timings"]

        status: int = e["response"]["status"]
        method = req["method"]

        resourceType = self.getResourceType(e)

        statusCodeText = ConUtils.colorizeStatusCode(status)
        urlText = ConUtils.colorizeUrlByResourceType(req["url"], resourceType)

        print("[" + str(id) + "] ——— " + statusCodeText + " " + method + " " + urlText)
        print("")

        startTime = 0
        endTime = startTime + int(e["time"])
        if ("_fromCache" in e):
            print("Cached: " + e["_fromCache"])
        print("Timestamp: " + e["startedDateTime"])
        print("Timing: "+ self.makeWaterfall(startTime, endTime, timings) +
            " (" + str(int(e["time"])) +" ms)")
        if ("_blocked_queueing" in timings and int(timings["_blocked_queueing"]) > 0):
            print("    queued  ( ): " + str(int(timings["_blocked_queueing"])) + " ms")
        if (int(timings["blocked"]) > 0):
            print("    blocked (-): " + str(int(timings["blocked"])) + " ms")
        if (int(timings["dns"]) > 0):
            print("    dns    : " + str(int(timings["dns"])) + " ms")
        if (int(timings["ssl"]) > 0):
            print("    ssl    : " + str(int(timings["ssl"])) + " ms")
        if (int(timings["connect"]) > 0):
            print("    connect    : " + str(int(timings["connect"])) + " ms")
        print("    send    (↑): " + str(int(timings["send"])) + " ms")
        print("    wait    (#): " + str(int(timings["wait"])) + " ms")
        print("    receive (↓): " + str(int(timings["receive"])) + " ms")
        print("")
        if (self.isHasBody(req)):
            print(ConUtils.colorizeText("REQUEST —————> " + req["postData"]["mimeType"] + ": ", fgColors.YELLOW))
        else:
            print(ConUtils.colorizeText("REQUEST —————> " + resourceType + " :", fgColors.YELLOW))
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

        if (resourceType == "websocket"):
            print("")
            print(ConUtils.colorizeText("WEBSOCKET:", fgColors.YELLOW))
            print(ConUtils.shorten(ConUtils.prettyContent(e["_webSocketMessages"]), self.truncateContent))

    def printRequestsTable(self, resType, reqType, filter):
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
            host = ConUtils.selectHostFromUrl(url)
            req = e["request"]
            res = e["response"]
            timings = e["timings"]

            if (host != ""):
                if (host not in hosts):
                    hostPlaceholder = "{" + str(len(hosts) + 1) + "}"
                    hosts.append(str(host))
                else:
                    hostPlaceholder = "{" + str(hosts.index(host) + 1) + "}"
                url = ConUtils.replaceHostInUrl(url, host, hostPlaceholder)

            resourceType = self.getResourceType(e)

            urlShorten = ConUtils.shorten(url, self.urlMaxLength)
            urlShorten = ConUtils.colorizeUrlByResourceType(urlShorten, resourceType)

            time = ConUtils.colorizeExecutionTime(int(e["time"]), "_fromCache" in e)
            statusCode = ConUtils.colorizeStatusCode(int(e["response"]["status"]))
            waterfall = self.makeWaterfall(startTime, completeTime, timings)

            if ((resType == "all" or replaceResType(resourceType) == resType) and
                (reqType == "all" or req["method"].lower() == reqType) and
                (filter == "" or (filter.lower() in url.lower()))):
                t.add_row([id, req["method"], statusCode, urlShorten, time, waterfall])
                self.lastShowedIds.append(id)
        print(t)

        for id, host in enumerate(hosts):
            print("{" + str(id + 1) + "} = " + host)

        completeTimeHumanized = humanize.naturaldelta(timedelta(microseconds=completeTime * 1000))
        print("Total recorded time: " + str(completeTimeHumanized) + " (" + str(completeTime) + " ms)")

    def copyRequestContent(self):
        if (self.selectedEntry == {}):
            print("No request content available")
            return

        method = self.selectedEntry["request"]["method"]
        if ((method == "POST" or method == "PUT" or method == "DELETE") and self.selectedEntry["request"]["bodySize"] > 0):
            if (self.selectedEntry["request"]["postData"]["mimeType"] == "application/json"):
                pyperclip.copy(ConUtils.prettyContent(self.selectedEntry["request"]["postData"]["text"]))
            else:
                pyperclip.copy(ConUtils.prettyContent(self.selectedEntry["request"]["postData"]["params"]))
            print("Request content copyied to clipboard")
        else:
            pyperclip.copy(ConUtils.prettyContent(self.selectedEntry["request"]["queryString"]))

    def copyResponseContent(self):
        if (self.selectedEntry != {} and self.selectedEntry["response"]["content"]["size"] > 0):
            text = ConUtils.prettyContent(self.selectedEntry["response"]["content"]["text"])
            pyperclip.copy(text)
            print("Response content copyied to clipboard")
        else:
            print("No response content available")

    def copyWebsocketContent(self):
        if (self.selectedEntry != {} and self.selectedEntry["_resourceType"] == "websocket"):
            print("WebSocket content copyied to clipboard")
            pyperclip.copy(ConUtils.prettyContent(self.selectedEntry["_webSocketMessages"]))
        else:
            print("No WebSocket content available")

    def printRequestContent(self):
        if (self.selectedEntry == {}):
            print("No request content available")
            return

        res = ""
        print("Request content:")

        method = self.selectedEntry["request"]["method"]
        if ((method == "POST" or method == "PUT" or method == "DELETE") and self.selectedEntry["request"]["bodySize"] > 0):
            if (self.selectedEntry["request"]["postData"]["mimeType"] == "application/json"):
                res = ConUtils.prettyContent(self.selectedEntry["request"]["postData"]["text"])
            else:
                res = ConUtils.prettyContent(self.selectedEntry["request"]["postData"]["params"])
            print(res)
        else:
            print(ConUtils.prettyContent(self.selectedEntry["request"]["queryString"]))

    def printResponseContent(self):
        if (self.selectedEntry != {} and self.selectedEntry["response"]["content"]["size"] > 0):
            res = ConUtils.prettyContent(self.selectedEntry["response"]["content"]["text"])
            print("Response content:")
            print(res)
        else:
            print("No response content available")

    def printWebsocketContent(self):
        if (self.selectedEntry != {} and self.selectedEntry["_resourceType"] == "websocket"):
            print("Websocket content:")
            print(ConUtils.prettyContent(self.selectedEntry["_webSocketMessages"]))
        else:
            print("No WebSocket content available")