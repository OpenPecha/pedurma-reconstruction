# Simple test to detect nonspacing marks

import unicodedata

def isNSM(char):
    result = True if unicodedata.category(char) == "Mn" else False
    return result

chars = ['ཀ', 'ི', 'ྱ', 'ཱྀ', '༔']

for char in chars:
    print(f' {char}  is NSM: {isNSM(char)}')