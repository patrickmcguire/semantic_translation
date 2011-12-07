#!/usr/bin/python

import sexp
import typ
import random
import collections
import re

counter = 0

def score(s, produced):
  global counter
  global cache
  #if counter == 20:
  #  exit()
  print "score called"
  print s
  counter += 1
  subexps = sexp.subexps(s)
  #if s in subexps:
  #  subexps.remove(s)
  #print subexps
  splits = sum([sexp.split(s, subexp) for subexp in subexps], [])
  #print splits
  #for split in splits:
  #  print split
  #print
  if not splits:
    #print "hit bottom"
    #print
    #print 1
    return 1
  #print
  print sexp.pretty_lambda(s)
  for x in splits:
    print "  ", sexp.pretty_lambda(x[0]), "/", sexp.pretty_lambda(x[1])
  print
  scr = max([score_one_split(s, x[0], x[1], produced) for x in splits])
  #print scr
  return scr

def make_cache_key(s, s1, s2):
  #return str(s) + "___" + str(s1) + "___" + str(s2)
  return str(s1) + "___" + str(s2)

hit = 0
miss = 0

def score_one_split(s, s1, s2, produced):
  global hit, miss, cache
  key = make_cache_key(s, s1, s2)
  if key in produced:
    return -99999
  nproduced = dict(produced)
  nproduced[key] = True
  if key in cache:
    hit += 1
    return cache[key]
  else:
    miss += 1
    scr = score(s1, nproduced) + score(s2, nproduced)
    cache[key] = scr
    return scr


def random_derivation(s, depth = 0, category = 'S', productions_above = []):
  global lexicon

  #for i in range(depth):
  #  print ' ',
  key = sexp.pretty_lambda(s)
  #print key

  if key in lexicon:
    #print lexicon[key]
    options = [l for l in lexicon[key] if l[0].replace('/', '|').replace('\\',
    '|') == category]
    if len(options) == 0:
      return False
    picked = random.sample(options, 1)[0]
    return [key, picked[0], picked[1]]

  if sexp.totally_vacuous(s):
    return False

  if depth > 3:
    return False

  splits = sum([sexp.split(s, sub) for sub in sexp.subexps(s)], [])
  if not splits:
    return False
  random.shuffle(splits)
  for split in splits:
    #print sexp.pretty_lambda(split[0]) + " : " + sexp.pretty_lambda(s[1])
    #print
    #print '\n'.join([sexp.pretty_lambda(s[0]) + " : " + sexp.pretty_lambda(s[1]) for s in productions_above])
    #print
    #print split in productions_above
    #print
    #print


    f = split[0]
    g = split[1]
    fcat = catf(f)
    if '|' in fcat:
      fcat2 = '(%s)' % fcat
    else:
      fcat2 = fcat
    gcat = '%s|%s' % (category, fcat2)
    #print category, fcat, gcat

    #print f, g
    #exit()

    d1 = random_derivation(split[0], depth+1, fcat, productions_above + [split])
    d2 = random_derivation(split[1], depth+1, gcat, productions_above + [split])
    if d1 and d2:
      return [key, category, d1, d2]
  return False
  #assert False
  #if depth == 2:
    #for split in splits:
    #  print ">", sexp.pretty_lambda(split[0])
    #  print ">", sexp.pretty_lambda(split[1])
    #  print
  #if depth < 10:
  #  picked = splits[random.randint(0,len(splits)-1)]
  #  random_derivation(picked[0], depth+1)
  #  random_derivation(picked[1], depth+1)

def catf(exp):
  sigs = sexp.typ(exp).signatures
  assert len(sigs) == 1
  sig = sigs.pop()
  return catf_t(sig)

def catf_t(t):
  if t == 'e':
    return 'NP'
  elif t == 't':
    return 'S'
  else:
    l = catf_t(t[1])
    r = catf_t(t[0])
    if '|' in r:
      r = '(' + r + ')'
    return l + '|' + r

def categorize(s):
  if s[1]:
    return
  categorize(s[2])
  categorize(s[3])
  intag = s[2][1].replace("\\", "|").replace("/", "|")
  outtag = s[3][1]

  m = re.search(r"[A-Z]+$|\([A-Z\|\\\/]+\)$", outtag)
  end = m.group(0).replace("\\", "|").replace("/", "|")
  if end[0] == '(':
    send = end[1:][:-1]
  else:
    send = end

  #print
  #print "in", intag
  #print "out", outtag

  #assert intag == send
  if not (intag == send):
    print "THIS WILL FAIL"

  #print re.search(r"[A-Z]+$", outtag)

  #print intag
  #print outtag[-len(intag):]
  #assert intag == outtag[-len(intag):]

  direction = outtag[-len(end)-1]
  newtag = outtag[:-len(end)-1]

  #print "new", newtag

  s[1] = newtag
  s.append(direction)

def pp(s, depth = 0):
  for i in range(depth):
    print ' ',
  if isinstance(s, str):
    print s
    return
  print s[0], s[1]
  if len(s) == 4:
    pp(s[2], depth+1)
    pp(s[3], depth+1)
  else:
    pp(s[2], depth+1)

def pp2(s, depth = 0):
  for i in range(depth):
    print ' ',
  print s['key'], s['score'],
  if 'terminals' in s:
    print s['terminals'],
  print
  if 'left' in s:
    pp2(s['left'], depth+1)
    pp2(s['right'], depth+1)

def flatten(s):
  if len(s) == 4:
    if s[4] == '\\':
      flatten(s[2])
      flatten(s[3])
    else:
      flatten(s[3])
      flatten(s[2])
  else:
    print s[2]


def split_potential(sent, split):
  return 0

def choose_lex_entry(key, category):
  global lexicon
  options = [l for l in lexicon[key] if l[0].replace('/', '|').replace('\\',
  '|') == category]
  if len(options) == 0:
    return False
  picked = options[0]
  #picked = random.sample(options, 1)[0]
  #return [key, picked[0], picked[1]]
  return picked[1]


def make_categories(split, category):
  (f, g) = split
  fcat = catf(f)
  if '|' in fcat:
    fcat2 = '(%s)' % fcat
  else:
    fcat2 = fcat
  gcat = '%s|%s' % (category, fcat2)
  return (fcat, gcat)

def all_lex_entries(key, category):
  global lexicon
  options = [l[1] for l in lexicon[key] if l[0].replace('/', '|').replace('\\',
    '|') == category]
  return options

def lm_score(terminal, cky):
  if len(cky) == 0:
    return 1
  print cky, terminal
  exit()


counter = 0
cache = {}
def best_derivation(sent, category, cky=None, depth=0):

  global counter
  global cache
  global lexicon

  if cky == None:
    cky = []

  lkey = sexp.pretty_lambda(sent)
  key = lkey + ' ' + category

  #if key in cache:
  #  return cache[key]

  counter += 1

  if lkey in lexicon:
    terminals = all_lex_entries(lkey, category)
    scored = [(terminal, lm_score(terminal, cky)) for terminal in terminals]
    if terminals:
      r = {'key': key,
          'scored': scored}
    #terminal = choose_lex_entry(lkey, category)
    #if terminal:
    #  r = {'key': key,
    #       'score': 1,
    #       'terminal': terminal}
    else:
      r = False
    cache[key] = r
    return r

  if sexp.totally_vacuous(sent):
    r = False
    cache[key] = r
    return r

  if depth == 3:
    r = False
    return r

  subs = sexp.subexps(sent)
  splits = sum((sexp.split(sent, sub) for sub in subs), [])

  scores = []
  for split in splits:
    ncky = list(cky)
    (fcat, gcat) = make_categories(split, category)
    left = best_derivation(split[0], fcat, ncky, depth+1)
    if not left:
      continue
    right = best_derivation(split[1], gcat, ncky, depth+1)
    if not right:
      continue
    sc = left['score'] + right['score'] + split_potential(sent, split)
    scores.append({'key': key,
                   'score': sc,
                   'left': left,
                   'right': right})

  if not scores:
    return False
  r = max(scores, key=lambda x: x['score'])
  cache[key] = r
  return r


#s3 = ['lambda', '$0', 'e', ['and', ['state:t', '$0'], ['exists', '$1', ['and', ['state:t', '$1'], ['loc:t', 'mississippi_river:r', '$1'], ['next_to:t', '$0', '$1']]]]]

#s3 = ['argmin', '$0', ['and', ['state:t', '$0'], ['state:t', '$0']], ['population:i', '$0']]

#s3 = ['argmin', '$0', ['city:t', '$0'], ['population:i', '$0']]
s3 = ['lambda', '$0', 'e', ['and', ['state:t', '$0'], ['next_to:t', '$0', 'florida:s']]]
#s3 = ['lambda', '$0', 'e', ['and', ['state:t', '$0'], ['next_to:t', '$0',
#'mississippi_river:r']]]

#s3 = 'mississippi_river:r'

sexp.init()
#cache = {}
#print score(s3, {})

#print sexp.subexps(s3)
#spl = sexp.split(s3, ['state:t', '$0'])[0]

lexicon = collections.defaultdict(list)
f = open('ubl/experiments/geo250-lambda/lexicon')
for line in f.readlines():
  line = line.strip().split(":", 2)
  exp = line[-1].strip()
  lang = line[0].strip()
  cat = line[1][2:][:-1]
  lexicon[exp].append((cat,lang))
f.close()

#print spl
#print lexicon[sexp.pretty_lambda(spl[0])][0][1]
#spl2 = sexp.split(spl[1], ['population:i', '$1'])[0]
##print spl2
#print sexp.pretty_lambda(spl2[1])
#print lexicon[sexp.pretty_lambda(spl2[1])]

##
#der = random_derivation(s3)
der = best_derivation(s3, 'S')
#print der
#categorize(der)
#pp(der[0])
pp2(der)
#flatten(der)

print counter

#print hit, miss
#print cache
#print decode(s3, cache)
