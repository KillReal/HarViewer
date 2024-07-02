import json

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