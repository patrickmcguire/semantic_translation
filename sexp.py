#parse
#
#copy
#
#get_type
#
#check_type
#
#infer_type
#
#get_free_vars
#
#extract_functs
#
#get_sub_expressions

import re
from test import *

LAMBDA = 'lambda'

F_ARGMAX = 'argmax'
F_ARGMIN = 'argmin'
F_COUNT  = 'count'
F_SUM    = 'sum'
F_LT     = '<'
F_GT     = '>'
F_AND    = 'and'
F_OR     = 'or'
F_NOT    = 'not'

T_TRUTH  = 't'
T_INT    = 'i'
T_ENTITY = 'e'

# TODO avoid namespace conflicts
BASE_FUNCTS = {
    F_ARGMAX: [T_ENTITY, T_TRUTH, T_INT, T_ENTITY],
    F_ARGMIN: [T_ENTITY, T_TRUTH, T_INT, T_ENTITY],
    F_COUNT:  [T_ENTITY, T_TRUTH, T_INT],
    F_SUM:    [T_ENTITY, T_TRUTH, T_INT, T_INT],
    F_LT:     [T_INT,    T_INT,   T_TRUTH],
    F_GT:     [T_INT,    T_INT,   T_TRUTH],
    F_AND:    [T_TRUTH,  T_TRUTH, T_TRUTH],
    F_OR:     [T_TRUTH,  T_TRUTH, T_TRUTH],
    F_NOT:    [T_TRUTH,  T_TRUTH, T_TRUTH],
}

BASE_TYPES = [
    T_TRUTH,
    T_INT,
    T_ENTITY,
]

__types__ = None
__functs__ = None

# TODO actually read
def read_lang_types():
  global __types__
  __types__ = list(BASE_TYPES)

def read_lang_functs():
  global __functs__
  __functs__ = dict(BASE_FUNCTS)
  f = open('corpora/geo-lambda.lang')
  for line in f.readlines()[1:-2]:
    parts = re.split(r"[\(\)\s]", line)
    name = parts[1]
    typ = parts[2:-2]
    btyp = [base_typ(t) for t in typ]
    __functs__[name] = btyp
  f.close()

def varp(sexp):
  return atomp(sexp) and sexp[0] == '$'

def atomp(sexp):
  return not isinstance(sexp, list)

def lambdap(sexp):
  return (not atomp(sexp)) and sexp[0] == LAMBDA

def applicationp(sexp):
  return not (atomp(sexp) or lambdap(sexp))

def functp(sexp):
  # atomp is probably unnecessary here
  global __functs__
  return atomp(sexp) and sexp in __functs__

def typ(sexp):
  global __functs__
  if atomp(sexp):
    if functp(sexp):
      return __functs__[sexp]
    elif varp(sexp):
      return T_ENTITY
    else:
      return annotated_type(sexp)
  elif lambdap(sexp):
    # not right
    return T_ENTITY
  elif applicationp(sexp):
    return application_typ(sexp)

def application_typ(sexp):

  funct_typ = typ(application_function(sexp))
  arg_typ = [typ(arg) for arg in application_args(sexp)]

  assert functp(application_function(sexp))

  funct_arg_typ = funct_typ[:-1]
  funct_return_typ = funct_typ[-1]

  assert same_typ(arg_typ, funct_arg_typ)
  return funct_return_typ

def annotated_type(atom):
  global __types__
  assert atomp(atom)
  colon_loc = atom.index(':')
  assert colon_loc >= 0
  typ = atom[colon_loc+1:]
  return base_typ(typ)

def application_function(sexp):
  assert applicationp(sexp)
  return sexp[0]

def application_args(sexp):
  assert applicationp(sexp)
  return sexp[1:]

def base_typ(typ):
  if typ in (T_TRUTH, T_INT):
    return typ
  return T_ENTITY

def same_typ(t1, t2):
  if isinstance(t1, list) and len(t1) == 1:
    t1 = t1[0]
  if isinstance(t2, list) and len(t2) == 1:
    t2 = t2[0]
  return t1 == t2

###

def init():
  read_lang_types()
  read_lang_functs()

###

def test():
  init()
  test_atomp()
  test_lambdap()
  test_applicationp()
  test_functp()
  test_typ()

def test_atomp():
  EXPECT_TRUE(atomp('atom'))
  EXPECT_FALSE(atomp(['funct', 'arg']))

def test_lambdap():
  EXPECT_TRUE(lambdap(['lambda', '$0', 'e', ['frob', '$0']]))
  EXPECT_FALSE(lambdap(['funct', 'arg']))
  EXPECT_FALSE(lambdap('atom'))

def test_applicationp():
  EXPECT_TRUE(applicationp(['funct', 'arg']))
  EXPECT_FALSE(applicationp(['lambda', '$0', 'e', 'atom']))
  EXPECT_FALSE(applicationp('atom'))

def test_functp():
  EXPECT_TRUE(functp(F_ARGMIN))
  EXPECT_FALSE(functp(LAMBDA))
  EXPECT_FALSE(functp('waffle'))
  EXPECT_FALSE(functp(['funct', 'arg']))

def test_typ():
  s1 = 'kansas:s'
  EXPECT_EQ(T_ENTITY, typ(s1))

  s2 = ['lambda', '$0', 'e', ['and', ['state:t', '$0'], ['exists', '$1', ['and', ['state:t', '$1'], ['loc:t', 'mississippi_river:r', '$1'], ['next_to:t', '$0', '$1']]]]]
  EXPECT_EQ(T_ENTITY, typ(s2))
  
  s3 = ['argmin', '$0', ['city:t', '$0'], ['population:i', '$0']]
  EXPECT_EQ(T_ENTITY, typ(s3))

  s4 = 'equals:t'
  EXPECT_EQ([T_ENTITY, T_ENTITY, T_TRUTH], typ(s4))

  s5 = ['city:t', ['equals:t', 'thing1:c', 'thing2:c']]
  try:
    typ(s5)
  except AssertionError:
    pass
  else:
    EXPECT_TRUE(False)
