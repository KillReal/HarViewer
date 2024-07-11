import json
import os
import re

class fgColors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    PURPLE = '\033[35m'
    YELLOW = '\033[93m'
    GRAY = '\033[90m'
    GRAY = '\033[90m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4'
    GRAYUNDERLINE = '\033[4;90m'

class ConUtils:
    @staticmethod
    def shorten(s, width, placeholder='...'):
        return s[:width] if len(s) <= width else s[:width-len(placeholder)] + placeholder

    @staticmethod
    def timeToMs(timestamp):
        return timestamp.total_seconds() * 1000
    
    @staticmethod   
    def prettyContent(content):
        try:
            content = json.loads(content)
        except:
            ()
        return json.dumps(content, indent = 4)

    @staticmethod
    def prettyJson(content):
        return json.dumps(content, indent = 4)
    
    @staticmethod
    def copyHostFromUrl(url):
        urlRegex = "(.*://[A-Za-z_0-9.:-]+).*"

        m = re.search(urlRegex, url)
        if m:
            return m.group(1)
        return ""

    @staticmethod
    def replaceHostInUrl(url, domain, placeholder = "{host}"):
        return url.replace(domain, placeholder)

    @staticmethod 
    def clear():
        os.system('cls' if os.name=='nt' else 'clear')

    @staticmethod
    def colorizeStatusCode(statusCode: int):
        if (statusCode >= 200 and statusCode < 300):
            statusCode = fgColors.GREEN + str(statusCode) + fgColors.ENDC
        elif (statusCode >= 300 and statusCode < 400):
            statusCode = fgColors.YELLOW + str(statusCode) + fgColors.ENDC
        elif (statusCode >= 400 and statusCode < 500):
            statusCode = fgColors.PURPLE + str(statusCode) + fgColors.ENDC
        elif (statusCode >= 500 or statusCode == 0):
            statusCode = fgColors.RED + str(statusCode) + fgColors.ENDC

        return statusCode
    
    @staticmethod
    def colorizeUrlByResourceType(url, resType):
        if (resType == "xhr"):
            url = fgColors.BLUE + url + fgColors.ENDC
        # elif (resType == "script"):
        #     url = fgColors.YELLOW + url + fgColors.ENDC
        elif (resType == "document"):
            url = fgColors.PURPLE + url + fgColors.ENDC
        elif (resType == "websocket"):
            url = fgColors.CYAN + url + fgColors.ENDC
        # elif (resType == "image"):
        #     url = fgColors.GREEN + url + fgColors.ENDC
        # elif (resType == "stylesheet" or resType == "font"):
        #     url = fgColors.RED + url + fgColors.ENDC

        return url

    @staticmethod
    def colorizeExecutionTime(time: int, isCached: bool):
        if (isCached):
            return fgColors.GRAYUNDERLINE + str(time) + fgColors.ENDC
        
    @staticmethod
    def colorizeText(text: str, color: fgColors):
        return color + text + fgColors.ENDC