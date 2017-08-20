#!/usr/bin/python
# coding: utf-8

# Copyright Pieter Kelchtermans 2017
# Tested on latest Windows, macOS and GNU/Linux versions.

# This file sets up a window with two text fields: one you can type in, 
# and one that the computer uses to suggest words you would want to type next.
#
# Those words are 'learnt' from the characters of your favorite TV Series.
# I chose as example Curb Your Enthusiasm, Season 6. If I would type
#     ME: The
# the algorithm suggests
#     AI: party point new
# and if I would follow up and continue
#     ME: The party
# I get
#     AI: was The Where's
#     ME: The party was
#     AI: last yesterday tonight
#
# In short: you can write whatever and get reminded of how your favorite
# characters would finish your sentences. Above, the algorithm was probably 
# thinking of this episode: https://www.youtube.com/watch?v=wubgGq9Mio4

try:
    import tkinter as Tkinter
    import urllib.request as urllib2
except ImportError:
    import urllib2
    import Tkinter

import collections
from io import BytesIO
import re
import os
import sys
import zipfile

tokens = [] # all individual words from a season, in the order they are spoken.
ngramlist = [] # lists of n-grams, 
# An n-gram is in this case a list of sequential words. https://en.wikipedia.org/wiki/N-gram
suggestionlist = [] # per n-gram, count how many times a specific word follows

max_n = 5 # maximum length of n-grams that are used to get matches
num_suggestions = 3 # number of suggested words in the bottom pane

# url of a zip archive of subtitles (change language, series ID, and season number to your liking)
target_url = "https://www.opensubtitles.org/download/s/sublanguageid-eng/pimdbid-264235/season-6"
if len(sys.argv) > 1:
    target_url = sys.argv[1]

# filter out non-word symbols and turn a string of words into a list
def tokenize(text):
    return re.sub('[%@#!.,-?"]', "", text).split()

# return all sequential n-length lists in a list
def nlists(input_list, n):
    return list(zip(*[input_list[i:] for i in range(n)]))
    
# Construct a dictionary with n-grams as keys
# and store words that come after each n-gram in a Counter
def makesuggestions(ngrams, n):
    result = {}

    for i in range(n, len(ngrams)):
        whatfollows = ngrams[i][0]
        if ngrams[i-n] not in result:
            result[ngrams[i-n]] = collections.Counter()
        result[ngrams[i-n]][whatfollows] += 1
    return result

# Make the list of all subtitled words from an opensubtitles season zip file,
with zipfile.ZipFile(BytesIO(urllib2.urlopen(target_url).read())) as z:
    for filename in z.namelist():
        if not os.path.isdir(filename):
            with z.open(filename) as file:
                for line in file:
                    line = line.decode('utf-8', "ignore")
                    if re.match("0-9", line) == None: #srt files contain time lines and text lines, we want the text-only lines
                        tokens += tokenize(line)
# create a list of all lengths of n-grams,
    for n in range(1,max_n+1):
        ngramlist.append(nlists(tokens, n))
# and create a dictionary of word suggestions for each n-gram.
    for n in range(1, max_n + 1):
        suggestionlist.append(makesuggestions(ngramlist[n-1], n))

# Start with finding the longest n-gram allowed at the tail of a supplied list of words.
# If the dictionary of n-grams of that length has follow-up words,
# add them to the result list.
# If that dictionary is exhausted, try finding a shorter n-gram to match.
def getsuggestions(words, n):
    result = []
    for length in reversed(range(1, max_n+1)):
        if len(words) > length - 1:
            ngram = tuple(words[-length:])
            if ngram in suggestionlist[length-1]:
                mostcommon = suggestionlist[length-1][ngram].most_common(n)
                for i in range(len(mostcommon)):
                    suggestion = mostcommon[i][0] #the word, not the count
                    if not suggestion in result and len(result) != n:
                        result.append(suggestion)
    
    return result

# Replace a text field's contents with a list of words
def insert(words, textfield):
    deleted = False
    for w in words:
        suggestion = w + " "
        if not deleted:
            textfield.delete(1.0, 'end')
            deleted = True
        textfield.insert('end', suggestion)

# Analyze the typing of one text field and put suggestions in another
def typing(event):
    typed = tokenize(typingtextfield.get(1.0, 'end'))
    suggestions = getsuggestions(typed, num_suggestions)
    insert(suggestions, suggestionstextfield)

main = Tkinter.Tk()

typingtextfield = Tkinter.Text(main)
typingtextfield.bind('<KeyRelease>', typing)
typingtextfield.grid()

suggestionstextfield = Tkinter.Text(main)
suggestionstextfield.grid()

main.mainloop()
