import json
import string
import random

class Translator:
    def __init__(self, dictionaryFname):
        with open(dictionaryFname) as fp:
            self.dictionary = json.load(fp)
    
    def directTranslate(self, sentence):
        random.seed(0)
        translation = []
        tokens = string.split(sentence)
        words = []
        for token in tokens:
            words.append(token.lower())
        for word in words:
            if (word in self.dictionary) and (self.dictionary[word]):
                translation.append(random.choice(self.dictionary[word]))
            else:
                translation.append(word)
        result = translation[0]
        for i in range(1,len(translation)):
            result = result + ' ' + translation[i]
        return result


def main():
    dictionaryFile = '../dic/dictionary.json'
    devSetFile = '../corpus/ita_dev.txt'
    sentences = []
    with open(devSetFile) as f:
        sentences = f.readlines()
    translator = Translator(dictionaryFile)
    for s in sentences:
        s = s.decode('utf-8')
        t = translator.directTranslate(s)
        print '\n'
        print t.encode('utf-8')
    
            
if __name__ == '__main__':
    main()
                
    
    