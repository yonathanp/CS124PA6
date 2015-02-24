import json
import re
import string
import sys
import random
from termcolor import colored, cprint


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
            cprint("ERROR (word not in dict): {0}".format(word.encode('utf-8')), 'yellow', file=sys.stderr)
            return word

        # If the word is in our dictionary but not defined, remain in Italian
        # TODO: remove when the dictionary is completely filled out
        if not self.italian_to_english[word]:
            cprint("ERROR (word has no definitions): {0}".format(word.encode('utf-8')), 'red', file=sys.stderr)
            return word

        # The naive translator simply returns a random definition for a given word
        return random.choice(self.italian_to_english[word])
        
        

class Translator:
    def __init__(self, dictionaryFname):
        self.dictionary = Dictionary(dictionaryFname)
        self.preprocessor = PreProcessor()
        self.postprocessor = PostProcessor()
    
    def directTranslate(self, sentence):
        # Seed RNG to 0 for debugging purposes
        random.seed(0)
        # Remove periods, commas
        sentence = re.sub('[.,]', '', sentence)
        # Clean hyphens surrounded by spaces
        sentence = re.sub(' - ', ' ', sentence)
        # Split up nell'ultima and friends
        sentence = re.sub("(\w)'(\w)", r"\1' \2", sentence, flags=re.U)

        # Split up our sentence into tokens and preprocess
        tokens = re.split(r"(?:[ ]+)", sentence.strip())
        words = self.preprocessor.process(tokens)

        # Translate
        translation = []
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
