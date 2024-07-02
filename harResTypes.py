from enum import Enum

class harResTypes(str, Enum):
    document = 'doc'
    stylesheet = 'css'
    image = 'img'
    script = 'js'

@staticmethod
def replaceResType(resType):
    def replace(x):
        try:
            return harResTypes[x].value
        except KeyError:
            return x

    return replace(resType)