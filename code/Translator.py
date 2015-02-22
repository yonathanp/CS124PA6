import json
import string
import random

class PreProcessor:
    def __init__(self):
        pass
    def process(self, sentence):
        return [x.lower() for x in sentence]

class PostProcessor:
    def __init__(self):
        pass
    def process(self, sentence):
        return sentence

class Dictionary:
    def __init__(self, dictionary_filename):
        with open(dictionary_filename) as f:
            self.italian_to_english = json.load(f)

    def translate_word(self, sentence, word_index):
        word = sentence[word_index]
        
        # Unknown words will remain in Italian
        if word not in self.italian_to_english:
            return word

        # If the word is in our dictionary but not defined, remain in Italian
        # TODO: remove when the dictionary is completely filled out
        if not self.italian_to_english[word]:
            return word

        # The naive translator simply returns a random definition for a given word
        return random.choice(self.italian_to_english[word])
        
        

class Translator:
    def __init__(self, dictionaryFname):
        self.dictionary = Dictionary(dictionaryFname)
        self.preprocessor = PreProcessor()
        self.postprocessor = PostProcessor()
    
    def directTranslate(self, sentence):
        random.seed(0)
        translation = []
        tokens = string.split(sentence)
        # Preprocess
        words = self.preprocessor.process(tokens)

        # Translate
        for i in range(len(words)):
            translation.append(self.dictionary.translate_word(words, i))

        # Postprocess
        translation = self.postprocessor.process(translation)

        return ' '.join(translation)


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
