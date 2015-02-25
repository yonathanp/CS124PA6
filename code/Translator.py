from __future__ import print_function
from pattern import en
import json
import os
import re
import string
import sys
import random
#from termcolor import colored, cprint


class PreProcessor:
    def __init__(self, config):
        self.config = config
        pass
    def process(self, sentence):
        for tok in sentence:
            tok['ita'] = tok['ita'].lower()
        return sentence

class PostProcessor:
    def __init__(self, config):
        self.config = config
        pass
    def process(self, sentence):
        #for i in range(len(en_sentence)):
        #    print(en_sentence[i][0])
        #    print(en_sentence[i][1])
        #    print("")
        #    if en_sentence[i][1] == "NOM":
        #        en_sentence[i][0] = en.pluralize(en_sentence[i][0])
        return sentence

class Dictionary:
    def __init__(self, config):
        self.config = config
        with open(config['dictionary_file']) as f:
            self.italian_to_english = json.load(f)
        with open(config['celex_file']) as celex:
            self.celex_frequencies = json.load(celex)

    def translate_word_random(self, sentence, word_index):
        word = sentence[word_index]['ita']
        word_type = sentence[word_index]['pos']

        # Punctuation is simply returned as it was
        if word_type == "PON" or word_type == "SENT":
            sentence[word_index]['en'] = word
            return
        
        # Unknown words will remain in Italian
        if word not in self.italian_to_english:
            print("ERROR (word not in dict): {0}".format(word.encode('utf-8')), file=sys.stderr)
            sentence[word_index]['en'] = word
            return

        # If the word is in our dictionary but not defined, remain in Italian
        # TODO: remove when the dictionary is completely filled out
        if not self.italian_to_english[word]:
            print("ERROR (word has no definitions): {0}".format(word.encode('utf-8')), file=sys.stderr)
            sentence[word_index]['en'] = word
            return

        # The naive translator simply returns a random definition for a given word
        sentence[word_index]['en'] = random.choice(self.italian_to_english[word])
        
    def translate_word_celex(self, sentence, word_index):
        self.translate_word_unigram(sentence, word_index, self.celex_frequencies)
        
    def translate_word_unigram(self, sentence, word_index, unigramFrequencies):
        word = sentence[word_index]['ita']
        word_type = sentence[word_index]['pos']
        if word_type == "PON" or word_type == "SENT":
            sentence[word_index]['en'] = word
            return
        if word not in self.italian_to_english:
            print("ERROR (word not in dict): {0}".format(word.encode('utf-8')), file=sys.stderr)
            sentence[word_index]['en'] = word
            return
        if not self.italian_to_english[word]:
            print("ERROR (word has no definitions): {0}".format(word.encode('utf-8')), file=sys.stderr)
            sentence[word_index]['en'] = word
            return
        maxFreq = 0.0
        bestTranslation = random.choice(self.italian_to_english[word])
        for w in self.italian_to_english[word]:
            if w in unigramFrequencies and unigramFrequencies[w] > maxFreq:
                maxFreq = unigramFrequencies[w]
                bestTranslation = w
        sentence[word_index]['en'] = bestTranslation
        
    def getAllEnglishWords(self):
        res = set()
        for i in self.italian_to_english:
            for e in self.italian_to_english[i]:
                res.add(e)
        return res
        
        

class Translator:
    def __init__(self, config):
        self.dictionary = Dictionary(config)
        self.preprocessor = PreProcessor(config)
        self.postprocessor = PostProcessor(config)
        self.config = config
        if(config['use_unigram']):
            self.unigramFrequencies = self.buildNGramModel(1, self.config['english_full_proceedings_file'],50)
    
    def directTranslate(self, sentence):
        # Seed RNG to 0 for debugging purposes
        random.seed(0)

        # Split up our sentence into tokens and preprocess
        sentence = self.preprocessor.process(sentence)

        # Translate
        if self.config['use_celex']:
            for i in range(len(sentence)):
                self.dictionary.translate_word_celex(sentence, i)
        else:
            for i in range(len(sentence)):
                self.dictionary.translate_word_random(sentence, i)

        # Postprocess
        sentence = self.postprocessor.process(sentence)

        return sentence
        
    def buildNGramModel(self, N, fname, skipLines):
        relevantWords = self.dictionary.getAllEnglishWords()
        Frequencies = {}
        with open(fname) as f:
            lines = f.readlines()
        boundry = min(len(lines),self.config['full_proceedings_lines_to_process'])
        for i in range(skipLines, boundry):
            line = lines[i].decode('utf-8')
            tokens = string.split(line)
            lcase = [token.lower() for token in tokens]
            words = [re.sub('[\W]+','',w) for w in lcase]
            for i in range(len(words) - N + 1):
                L = words[i:i+N]
                relevant = True
                for w in L:
                    if relevantWords and (w not in relevantWords):
                        relevant = False
                if relevant:
                    key = ' '.join(L)
                    if key in Frequencies:
                        Frequencies[key] += 1
                    else:
                        Frequencies[key] = 1
        return Frequencies

def load_POS_sentences(f):
    sentences = []
    current_sentence = []
    for line in f:
        word, word_type, base = line.decode('utf-8').strip().split("\t")
        token = {'ita': word, 'pos': word_type, 'ita_base': base}
        current_sentence.append(token)
        if word == '.' and word_type == 'SENT':
            sentences.append(current_sentence)
            current_sentence = []
    return sentences

def main():
    # Ensure our working directory is correct
    os.chdir(sys.path[0])
    CONFIG_FILE = 'config.json'
    with open(CONFIG_FILE) as f:
        config = json.load(f)
    with open(config['dev_sentence_pos_file']) as f:
        dev_sentences = load_POS_sentences(f)
    with open(config['dev_gold_file']) as f:
        gold_sentences = f.readlines()
    translator = Translator(config)
    for (s, gold) in zip(dev_sentences, gold_sentences):
        t = translator.directTranslate(s)
        print("ITALIAN:")
        print(' '.join([x['ita'] for x in s]))
        print("TRANSLATION:")
        print(' '.join([x['en'] for x in s]))
        print("GOLD:")
        print(gold)
        print("")
        print("")


if __name__ == '__main__':
    main()
