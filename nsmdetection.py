import unicodedata

def isNSM(char):
    # Detects nonspacing mark characters
    isNSM = True if unicodedata.category(char) == "Mn" else False
    return isNSM

chars = ['ཀ', 'ི', 'ྱ', 'ཱྀ', '༔']

for char in chars:
    print(f' {char}  is NSM: {isNSM(char)}')




s = 'ད:ེ་'

s = '  ' + s[0] + s[2] + s[3] + s[1]

print(s)