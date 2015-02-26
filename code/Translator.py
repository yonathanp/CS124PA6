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
        if it.pluralize(tok['ita_base']) != tok['ita']:
            return
        
        # If singularizing the Italian word doesn't change it, it was singular
        if it.singularize(tok['ita_base']) == tok['ita']:
            return

        tok['en'] = en.pluralize(tok['en'])

    def conjugate_infinitives(self, tok):
        if tok['pos'] != 'VER:infi':
            return
        if it.conjugate(tok['ita_base']) != tok['ita']:
            return

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
        if it.conjugate(tok['ita_base'], it.PRESENT, 1, it.PL) == tok['ita']:
            tok['en'] = en.conjugate(tok['en'], en.PRESENT, 1, en.PL)
        elif it.conjugate(tok['ita_base'], it.PRESENT, 2, it.PL) == tok['ita']:
            tok['en'] = en.conjugate(tok['en'], en.PRESENT, 2, en.PL)
        elif it.conjugate(tok['ita_base'], it.PRESENT, 3, it.PL) == tok['ita']:
            tok['en'] = en.conjugate(tok['en'], en.PRESENT, 3, en.PL)
        elif it.conjugate(tok['ita_base'], it.PRESENT, 1, it.SG) == tok['ita']:
            tok['en'] = en.conjugate(tok['en'], en.PRESENT, 1, en.SG)
        elif it.conjugate(tok['ita_base'], it.PRESENT, 2, it.SG) == tok['ita']:
            tok['en'] = en.conjugate(tok['en'], en.PRESENT, 2, en.SG)
        elif it.conjugate(tok['ita_base'], it.PRESENT, 3, it.SG) == tok['ita']:
            tok['en'] = en.conjugate(tok['en'], en.PRESENT, 3, en.SG)
        else:
            return

        #print("CHANGE MADE, original then new")
        #print(original)
        #print(tok)
        return
 
    def add_overt_pronoun(self, sentence, i):
        tok = sentence[i]
        prev = None
        if i != 0:
            prev = sentence[i - 1]
        if tok['pos'] != 'VER:cpre' and tok['pos'] != 'VER:pres':
            return
        if i != 0 and (prev['pos'] == 'NOM' or prev['pos'].startswith("PRO")):
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

        #print("CHANGE MADE")
        #print(tok)
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

    def remove_useless_articles(self, sentence, i):
        if i == 0:
            return
        tok = sentence[i]
        prev = sentence[i-1]
        
        # This deletes "the my" and "the his"
        if prev['pos'] == 'DET:def' and tok['pos'] == "PRO:poss":
            del sentence[i - 1]
            #print("DELETING USELESS ARTICLE")
            #print(prev)
            #print(tok)
            return True

        # More advanced "the his" deletion
        if tok['pos'] == 'PRO:poss' and prev['en'].endswith(' the'):
            #print(sentence[i - 1])
            sentence[i - 1]['en'] = sentence[i - 1]['en'][0:-4]
            #print(sentence[i - 1])
            #print(sentence[i])



    def remove_reflexive_junk(self, sentence, i):
        tok = sentence[i]
        if tok['pos'] == "PRO:refl":
            del sentence[i]
            #print("FIXING REFLEXIVE")
            #print(tok)
            return True

    def remove_preposition_before_infinitive(self, sentence, i):
        tok = sentence[i]
        if tok['pos'] != 'VER:infi':
            return
        if it.conjugate(tok['ita_base']) != tok['ita']:
            return

        if i != 0:
            prev = sentence[i - 1]
            if prev['pos'] == 'PRE':
                del sentence[i - 1]
                return True


    def correct_a_an(self, sentence, i):
        if i == 0:
            return
        tok = sentence[i]
        prev = sentence[i - 1]
        if (tok['pos'] != 'NOM' and tok['pos'] != 'ADJ') or prev['pos'] != 'DET:indef':
            return

        prev['en'] = en.article(tok['en'])

        #print("CHANGING A/AN")
        #print(tok)
        #print(prev)

    def process(self, sentence):
        # Single word operations
        i = 0
        for tok in sentence:
            if self.config['use_pluralization']:
                self.pluralize_if_needed(tok)
            if self.config['use_verb_conjugation']:
                self.conjugate_past_english_verbs(tok)
                self.conjugate_english_verbs(tok)
                self.conjugate_future_english_verbs(tok)
                self.conjugate_gerunds(tok)
                self.conjugate_infinitives(tok)
            if self.config['use_overt_pronouns']:
                self.add_overt_pronoun(sentence, i)
            i += 1

        # Reordering operations
        i = 0
        for tok in sentence:
            if self.config['use_adjective_reordering']:
                self.reorder_adjectives(sentence, i)
            i += 1

        # Deletion operations
        i = 0
        for tok in sentence:
            if self.config['remove_useless_material']:
                if self.remove_useless_articles(sentence, i):
                    i -= 1
                if self.remove_reflexive_junk(sentence, i):
                    i -= 1
                if self.remove_preposition_before_infinitive(sentence, i):
                    i -= 1
            i += 1

        # Multi-word operations
        i = 0
        for tok in sentence:
            if self.config['use_a_an_correction']:
                self.correct_a_an(sentence, i)
            i += 1


        return sentence

class Dictionary:
    def __init__(self, config):
        self.config = config
        with open(config['dictionary_file']) as f:
            self.italian_to_english = json.load(f)
        english_words = set()
        for itw in self.italian_to_english:
            for enw in self.italian_to_english[itw]:
                english_words.add(enw)
        with open(config['celex_file']) as celex:
            self.celex_frequencies = json.load(celex)
        if config['use_pos_filtering_for_translation']:
            with open(config['pos_dictionary_file']) as f:
                dictionary_pos = json.load(f) 
            self.english_dictionary_pos = {}
            for w in english_words:
                if w in dictionary_pos:
                    self.english_dictionary_pos[w] = dictionary_pos[w]
            with open(config['pos_mapping_file']) as f:
                # a mapping between english POS tags and a regular expression that represents 
                self.pos_mapping = json.load(f)
                
    def pos_translation_filter(self, sentence, word_index):
        word_type = sentence[word_index]['pos']
        word = sentence[word_index]['ita']
        if word_type == "PON" or word_type == "SENT":
            return
        relevant_translations = []
        for w in self.italian_to_english[word]:
            if w not in self.english_dictionary_pos:
               relevant_translations.append(w)
            else:  
                for edp in self.english_dictionary_pos[w]:
                    m = re.match(self.pos_mapping[edp], word_type)
                    if m != None:
                        relevant_translations.append(w)
        relevant_translations_set = set(relevant_translations)
        if relevant_translations_set:
            self.italian_to_english[word] = list(relevant_translations_set)

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
        randomTrans = True
        for w in self.italian_to_english[word]:
            if w in unigramFrequencies and unigramFrequencies[w] > maxFreq:
                maxFreq = unigramFrequencies[w]
                bestTranslation = w
                randomTrans = False
        sentence[word_index]['en'] = bestTranslation
        return randomTrans
        
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
        if self.config['use_pos_filtering_for_translation']:
            for i in range(len(sentence)):
                self.dictionary.pos_translation_filter(sentence, i)
                
        if self.config['use_unigram']:
            for i in range(len(sentence)):
                randomTrans = self.dictionary.translate_word_unigram(sentence, i, self.unigramFrequencies)
                if randomTrans and self.config['use_celex']:
                    self.dictionary.translate_word_celex(sentence, i)
        elif self.config['use_celex']:
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
