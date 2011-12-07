#!/usr/bin/python

import collections
import sexp
import typ
import re

import nltk

class Cell:
  def __init__(self, word, prev, score):
    self.word = word
    self.prev = prev
    self.score = score
  
  def set_chart(self, chart):
    self.chart = chart

class Chart:
  def __init__(self, sent, category):
    self.cells = []
    self.sent = sent
    self.category = category

  def add(self, cell):
    self.cells.append(cell)

  def add_all(self, chart):
    for cell in chart.cells:
      self.cells.append(cell)

  def keep(self, n):
    # TODO faster?
    self.cells.sort(key=lambda x: x.score)
    self.cells = self.cells[:n]

  def str(self):

    for cell in self.cells:
      c = cell
      while True:
        if not c.prev:
          break
        print '%s (%f)' % (c.word, c.score),
        c = c.prev

      print

class Decoder:

  MAX_DEPTH = 3
  BEAM_WIDTH = 20

  def __init__(self):
    self.lexicon = collections.defaultdict(list)
    f = open('ubl/experiments/geo250-lambda/lexicon')
    for line in f.readlines():
      line = line.strip().split(":", 2)
      exp = line[-1].strip()
      lang = line[0].strip()
      cat = line[1][2:][:-1]
      self.lexicon[exp].append((cat,lang))
    f.close()

    print 'building lm....'
    estimator = lambda fdist, bins: nltk.probability.LidstoneProbDist(fdist, 0.2)
    #lower_brown = (word.lower() for word in nltk.corpus.brown.words())
    lower_brown = nltk.corpus.brown.words()
    self.lm = nltk.NgramModel(2, lower_brown, estimator)
    print 'done.'

  def lex_entries(self, key, category):
    if not key in self.lexicon:
      return False
    options = [l[1] for l in self.lexicon[key] if l[0].replace('/',
      '|').replace('\\', '|') == category]
    return options

  def lm_score(self, w, c):
    wp = w.split()
    cp = c.split()

    word = wp[0]
    context = cp[-1]

    if context == '<S>':
      return 0

    try:
      return self.lm.logprob(word, [context])
    except TypeError:
      #print "I don't know %s, %s" % (word, context)
      # we should do better
      return 30
    #if w1p[-1] == 'the' and w2p[0] == 'is':
    #  return -1
    #return 0

  def new_cell(self, word, chart):
    scored = [(cell, self.lm_score(word, cell.word)) for cell in chart.cells]
    (prev, score) = max(scored, key=lambda x: x[1])
    return Cell(word, prev, score)

  def make_categories(self, split, category):
    (f, g) = split
    fcat = self.catf(f)
    if '|' in fcat:
      fcat2 = '(%s)' % fcat
    else:
      fcat2 = fcat
    gcat = '%s|%s' % (category, fcat2)
    return (fcat, gcat)

  def catf(self, exp):
    sigs = sexp.typ(exp).signatures
    assert len(sigs) == 1
    sig = sigs.pop()
    return self.catf_t(sig)

  def catf_t(self, t):
    if t == 'e':
      return 'NP'
    elif t == 't':
      return 'S'
    else:
      l = self.catf_t(t[1])
      r = self.catf_t(t[0])
      if '|' in r:
        r = '(' + r + ')'
      return l + '|' + r

  def decode(self, sent, category, chart, depth=0):

    if len(chart.cells) == 0:
      return False
      #TODO what's going on here?

    key = sexp.pretty_lambda(sent)

    les = self.lex_entries(key, category)
    if les:
      nchart = Chart(sent, category)
      for le in les:
        ncell = self.new_cell(le, chart)
        ncell.set_chart(nchart)
        nchart.add(ncell)
      return nchart

    if sexp.totally_vacuous(sent):
      return False

    if depth == self.MAX_DEPTH:
      return False

    splits = sexp.all_splits(sent)

    nchart = Chart(sent, category)
    for split in splits:
      (fcat, gcat) = self.make_categories(split, category)
      lchart = self.decode(split[0], fcat, chart, depth+1)
      if not lchart:
        continue
      lchart.keep(self.BEAM_WIDTH)
      rchart = self.decode(split[1], gcat, lchart, depth+1)
      if not rchart:
        continue
      nchart.add_all(rchart)
    nchart.keep(self.BEAM_WIDTH)
    return nchart

if __name__=='__main__':
  sexp.init()
  dec = Decoder()
  sent = ['lambda', '$0', 'e', ['and', ['state:t', '$0'], ['next_to:t', '$0', 'florida:s']]]
  cat = 'S'
  chart = Chart(sent, cat)
  cell = Cell('<S>', None, 0)
  cell.set_chart(chart)
  chart.add(cell)
  print dec.decode(sent, cat, chart).str()
