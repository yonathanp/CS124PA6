from __future__ import print_function
from pattern import en
from pattern import it
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
    def pluralize_if_needed(self, tok):
        # We only know how to pluralize nouns and adjectives
        if tok['pos'] != "NOM":
            return

        # Don't try and pluralize words with no known base words
        if tok['ita_base'] == "<unknown>":
            return

        # If pluralizing the Italian word alters it, then it was probably singular
        if it.pluralize(tok['ita']) != tok['ita']:
            return
        
        # If singularizing the Italian word doesn't change it, it was singular
        if it.singularize(tok['ita']) == tok['ita']:
            return

        tok['en'] = en.pluralize(tok['en'])

    def conjugate_infinitives(self, sentence, i):
        tok = sentence[i]
        original = tok['en']
        if tok['pos'] != 'VER:infi':
            return
        if it.conjugate(tok['ita_base']) != tok['ita']:
            return

        if i != 0:
            prev = sentence[i - 1]
            if prev['pos'] == 'PRE':
                del sentence[i - 1]

        tok['en'] = "to " + tok['en']
        return

    def conjugate_gerunds(self, tok):
        if tok['pos'] != 'VER:geru':
            return
        original = tok['en']
        tok['en'] = en.conjugate(tok['en'], aspect=en.PROGRESSIVE) 

        #print("CHANGE MADE, original then new")
        #print(original)
        #print(tok)
    def conjugate_future_english_verbs(self, tok):
        if tok['pos'] != 'VER:futu':
            return
        original = tok['en']
        tok['en'] = 'will ' + tok['en']

        #print("CHANGE MADE, original then new")
        #print(original)
        #print(tok)
        return
 
    def conjugate_past_english_verbs(self, tok):
        if tok['pos'] != 'VER:pper':
            return
        original = tok['en']
        # XXX: BUG IN pattern!!! You must pass in en.PROGRESSIVE instead of
        # en.PERFECTIVE due to a bug in pattern.en
        tok['en'] = en.conjugate(tok['en'], en.PAST, aspect=en.PROGRESSIVE)

        #print("CHANGE MADE, original then new")
        #print(original)
        #print(tok)
        return
 
    def conjugate_english_verbs(self, tok):
        original = tok['en']
        if tok['pos'] != 'VER:cpre' and tok['pos'] != 'VER:pres':
            return
        if it.conjugate(tok['ita'], it.PRESENT, 1, it.PL) == tok['ita']:
            tok['en'] = en.conjugate(tok['en'], en.PRESENT, 1, en.PL)
        elif it.conjugate(tok['ita'], it.PRESENT, 2, it.PL) == tok['ita']:
            tok['en'] = en.conjugate(tok['en'], en.PRESENT, 2, en.PL)
        elif it.conjugate(tok['ita'], it.PRESENT, 3, it.PL) == tok['ita']:
            tok['en'] = en.conjugate(tok['en'], en.PRESENT, 3, en.PL)
        elif it.conjugate(tok['ita'], it.PRESENT, 1, it.SG) == tok['ita']:
            tok['en'] = en.conjugate(tok['en'], en.PRESENT, 1, en.SG)
        elif it.conjugate(tok['ita'], it.PRESENT, 2, it.SG) == tok['ita']:
            tok['en'] = en.conjugate(tok['en'], en.PRESENT, 2, en.SG)
        elif it.conjugate(tok['ita'], it.PRESENT, 3, it.SG) == tok['ita']:
            tok['en'] = en.conjugate(tok['en'], en.PRESENT, 3, en.SG)
        else:
            return

        #print("CHANGE MADE, original then new")
        #print(original)
        #print(tok)
        return
 
    def add_overt_pronoun(self, tok):
        if tok['pos'] != 'VER:cpre' and tok['pos'] != 'VER:pres':
            return
        if it.conjugate(tok['ita'], it.PRESENT, 1, it.PL) == tok['ita']:
            tok['en'] = "we " + tok['en']
        elif it.conjugate(tok['ita'], it.PRESENT, 2, it.PL) == tok['ita']:
            tok['en'] = "you " + tok['en']
        elif it.conjugate(tok['ita'], it.PRESENT, 3, it.PL) == tok['ita']:
            tok['en'] = "they " + tok['en']
        elif it.conjugate(tok['ita'], it.PRESENT, 1, it.SG) == tok['ita']:
            tok['en'] = "I " + tok['en']
        elif it.conjugate(tok['ita'], it.PRESENT, 2, it.SG) == tok['ita']:
            tok['en'] = "you " + tok['en']
        elif it.conjugate(tok['ita'], it.PRESENT, 3, it.SG) == tok['ita']:
            tok['en'] = "it " + tok['en']
        else:
            return

        print("CHANGE MADE")
        print(tok)
        return

    def reorder_adjectives(self, sentence, i):
        if i == len(sentence) - 1:
            return
        tok = sentence[i]
        # Reordering only works on nouns
        if tok['pos'] != 'NOM':
            return

        move_to = i + 1
        while move_to < len(sentence):
            # If we find an adjective then we know where we want to move this to
            if sentence[move_to]['pos'] == 'ADJ':
                break
            # If there's a non-adverb between this noun and the next adjective then don't reorder
            if sentence[move_to]['pos'] != 'ADV':
                return

            move_to += 1

        if move_to == len(sentence):
            return
        for j in range(i, move_to):
            sentence[j] = sentence[j + 1]
        sentence[move_to] = tok
        #print("SWITCHING:")
        #for i in range(i, move_to + 1):
        #    print(sentence[i])
    def reorder_adverbs(self, sentence, i):
        if i == len(sentence) - 1:
            return
        tok = sentence[i]
        after = sentence[i + 1]
        if tok['pos'].startswith("VER:") and after['pos'] == 'ADV':
            sentence[i], sentence[i + 1] = sentence[i + 1], sentence[i]
            print("SWITCHING:")
            print(tok)
            print(after)


    def process(self, sentence):
        i = 0
        for tok in sentence:
            if self.config['use_pluralization']:
                self.pluralize_if_needed(tok)
            if self.config['use_verb_conjugation']:
                self.conjugate_past_english_verbs(tok)
                self.conjugate_english_verbs(tok)
                self.conjugate_future_english_verbs(tok)
                self.conjugate_gerunds(tok)
                self.conjugate_infinitives(sentence, i)
            #self.add_overt_pronoun(tok)
            if self.config['use_adjective_reordering']:
                self.reorder_adjectives(sentence, i)
            self.reorder_adverbs(sentence, i)
            i += 1

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
    i = 1
    target = None
    if len(sys.argv) != 1:
        target = int(sys.argv[1])
    for (s, gold) in zip(dev_sentences, gold_sentences):
        if target != None and i != target:
            i += 1
            continue
        t = translator.directTranslate(s)
        print("SENTENCE {0}".format(i))
        print("ITALIAN:")
        print(' '.join([x['ita'].encode('utf-8') for x in s]))
        print("TRANSLATION:")
        print(' '.join([x['en'].encode('utf-8') for x in s]))
        print("GOLD:")
        print(gold)
        if target != None:
            for x in s:
                print(x)
        #for x in s:
        #    print(x)
        print("")
        print("")
        i += 1


if __name__ == '__main__':
    main()
