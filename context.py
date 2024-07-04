import pyperclip
from conUtils import ConUtils
from harResTypes import replaceResType
import humanize
from prettytable import PrettyTable
import json
from datetime import datetime, timedelta

class Context:
    def __init__(self, urlMaxLength, waterfallMaxLength):
        self.urlMaxLength = urlMaxLength
        self.waterfallMaxLength = waterfallMaxLength
        self.entries = []
        self.lastEntry = {}
        self.truncateContent = 1000

    def makeWaterfall(self, startTime, completeTime, timings):
        step = completeTime / self.waterfallMaxLength

        blocked = timings["blocked"]
        send = timings["send"]
        wait = timings["wait"]
        recieve = timings["receive"]

        time = blocked + send + wait + recieve

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
        print("REQUEST —————> Cookies: ")
        print(ConUtils.prettyContent(self.lastEntry["request"]["cookies"]))
        print(" ")
        print("RESPONSE <————— Cookies: ")
        print(ConUtils.prettyContent(self.lastEntry["response"]["cookies"]))

    def printHeaders(self):
        if (self.lastEntry == {}):
            print("No header content available")
            return

        print(" ")
        print("REQUEST —————> Headers: ")
        print(json.dumps(self.lastEntry["request"]["headers"], indent = 4))
        print(" ")
        print("RESPONSE <————— Headers: ")
        print(json.dumps(self.lastEntry["response"]["headers"], indent = 4))

    def printRequestDetail(self, id):
        e = self.entries[id]
        self.lastEntry = e
        req = e["request"]
        res = e["response"]

        status = e["response"]["status"]
        method = req["method"]

        print("[" + str(id) + "] ——— " + str(status) + " " + method + " " + req["url"])
        print("")

        startTime = 0
        endTime = startTime + int(e["time"])

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
            print("REQUEST —————> " + req["postData"]["mimeType"] + ": ")
        else:
            print("REQUEST —————> " + e["_resourceType"] + " :")
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
        print("RESPONSE <————— " + res["content"]["mimeType"] +":")
        print("    Status: " + str(status))
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
            print("WEBSOCKET:")
            print(ConUtils.shorten(ConUtils.prettyContent(e["_webSocketMessages"]), self.truncateContent))

    def printRequests(self, har, resType, reqType, filter):
        self.entries = har["log"]["entries"]

        initTime = datetime.fromisoformat(self.entries[0]["startedDateTime"])
        latestEntry = max(self.entries, key=lambda x:x["startedDateTime"])

        completeTime = int(ConUtils.timeToMs(datetime.fromisoformat(latestEntry["startedDateTime"]) - initTime)
            + latestEntry["time"])

        hosts = []
        hostPlaceholder = "{host" + str(len(hosts) + 1) + "}"

        t = PrettyTable(['Id', 'Req', 'Res', 'Url', "Time", "Waterfall"])
        t.align = "l"
        for id, e in enumerate(self.entries):
            startTime = ConUtils.timeToMs(datetime.fromisoformat(e["startedDateTime"]) - initTime)
            url = e["request"]["url"]
            host = ConUtils.copyHostFromUrl(url)

            if (host != ""):
                if (host not in hosts):
                    hostPlaceholder = "{host" + str(len(hosts) + 1) + "}"
                    hosts.append(str(host))
                url = ConUtils.replaceHostInUrl(url, host, hostPlaceholder)

            if ((resType == "all" or replaceResType(e["_resourceType"]) == resType) and
                (reqType == "all" or e["request"]["method"].lower() == reqType) and
                (filter == "" or (filter.lower() in url.lower()))):
                t.add_row([id, e["request"]["method"], e["response"]["status"],
                    ConUtils.shorten(url, self.urlMaxLength), int(e["time"]),
                    self.makeWaterfall(startTime, completeTime, e["timings"])])
        print(t)

        for id, host in enumerate(hosts):
            print("{host" + str(id + 1) + "} = " + host)

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
            pyperclip.copy("")
            print("No response content available")

    def copyWebsocketContent(self):
        if (self.lastEntry != {} and self.lastEntry["_resourceType"] == "websocket"):
            print("WebSocket content copyied to clipboard")
            pyperclip.copy(ConUtils.prettyContent(self.lastEntry["_webSocketMessages"]))
        else:
            print("No WebSocket content available")