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
from util import *
from typ import Typ
from collections import defaultdict
import pprint

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
F_EXISTS = 'exists'

T_TRUTH  = 't'
T_INT    = 'i'
T_ENTITY = 'e'

BASE_FUNCTS = {
    F_ARGMAX: Typ.create((T_ENTITY, T_TRUTH, T_INT,   T_ENTITY)),
    F_ARGMIN: Typ.create((T_ENTITY, T_TRUTH, T_INT,   T_ENTITY)),
    F_COUNT:  Typ.create((T_ENTITY, T_TRUTH, T_INT)),
    F_SUM:    Typ.create((T_ENTITY, T_TRUTH, T_INT,   T_INT)),
    F_LT:     Typ.create((T_INT,    T_INT,   T_TRUTH)),
    F_GT:     Typ.create((T_INT,    T_INT,   T_TRUTH)),
    F_AND:    Typ.create_ambiguous([(T_TRUTH,  T_TRUTH, T_TRUTH),
                                    (T_TRUTH,  T_TRUTH, T_TRUTH, T_TRUTH)]),
    F_OR:     Typ.create_ambiguous([(T_TRUTH,  T_TRUTH, T_TRUTH),
                                    (T_TRUTH,  T_TRUTH, T_TRUTH, T_TRUTH)]),
    F_NOT:    Typ.create((T_TRUTH,  T_TRUTH, T_TRUTH)),
    # TODO this actually a macro, not a function
    F_EXISTS: Typ.create((T_ENTITY, T_TRUTH, T_TRUTH)),
}

BASE_TYPES = [
    T_TRUTH,
    T_INT,
    T_ENTITY,
]

QUANTIFIERS = [
    F_ARGMIN,
    F_ARGMAX,
    F_COUNT,
    F_SUM,
    F_EXISTS,
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

  typs = defaultdict(list)
  for line in f.readlines()[1:-2]:
    parts = re.split(r"[\(\)\s]", line)
    name = parts[1]
    typ = parts[2:-2]
    # marginally faster than w/o intermediate list
    btyp = tuple([base_typ(t) for t in typ])
    typs[name].append(btyp)
    #__functs__[name] = Typ.create(btyp)
  f.close()

  for name in typs:
    __functs__[name] = Typ.create_ambiguous(typs[name])

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

def quantifierp(sexp):
  return application_function(sexp) in QUANTIFIERS

def subexps_typed(sexp, t):
  return subexps(sexp, lambda x: Typ.check_equivalence(typ(x), t))

def free_variables(sexp):
  if atomp(sexp):
    if varp(sexp):
      return set([sexp])
    else:
      return set([])
  elif lambdap(sexp):
    var = lambda_arg_name(sexp)
    fvars = free_variables(lambda_body(sexp))
    #assert var in fvars
    if var in fvars:
      fvars.remove(var)
    return fvars
  elif applicationp(sexp):
    if quantifierp(sexp):
      var = quantifier_var(sexp)
      fvars = set()
      for arg in quantifier_args(sexp):
        fvars = fvars.union(free_variables(arg))
      if var in fvars:
        fvars.remove(var)
      return fvars
    else:
      fvars = set()
      for arg in application_args(sexp):
        fvars = fvars.union(free_variables(arg))
      fvars = fvars.union(free_variables(application_function(sexp)))
      return fvars
  else:
    assert False

def subexps(sexp, pred = lambda x: True):
  r = []
  if pred(sexp):
    r.append(sexp)
  if atomp(sexp):
    pass
  elif lambdap(sexp):
    r += subexps(lambda_body(sexp), pred)
  elif applicationp(sexp):
    r += sum([subexps(s, pred) for s in application_args(sexp)], [])
    #if not quantifierp(sexp):
    #if all(totally_vacuous(arg) for arg in application_args(sexp)):
    #  r += subexps(application_function(sexp))
  else:
    assert False
  return r

def all_splits(sexp):
  subs = subexps(sexp)
  return sum((split(sexp, sub) for sub in subs), [])

def replace_with_variable(sexp, subexp, variable):
  if sexp == subexp:
    return variable
  elif applicationp(sexp):
    start = 0
    if quantifierp(sexp):
      start = 2
    replaced = False
    for j in range(start, len(sexp)):
      replaced = replace_with_variable(sexp[j], subexp, variable)
      if replaced:
        break
    if replaced:
      copy = list(sexp)
      copy[j] = replaced
      return copy
    else:
      return False

  elif lambdap(sexp):
    newbody = replace_with_variable(lambda_body(sexp), subexp, variable)
    assert newbody
    copy = list(sexp)
    copy[3] = newbody
    return copy
  else:
    return False

def variables(sexp):
  if atomp(sexp):
    if varp(sexp):
      return set([sexp])
    else:
      return set()
  elif lambdap(sexp):
    return variables(lambda_body(sexp))
  elif applicationp(sexp):
    vrz = set()
    for arg in application_args(sexp):
      vrz = vrz.union(variables(arg))
    return vrz
  else:
    assert False

def type_in(var, sexp):
  if lambdap(sexp):
    if var == lambda_arg_name(sexp):
      return lambda_arg_typ(sexp)
    else:
      return type_in(var, lambda_body(sexp))
  elif applicationp(sexp):
    if quantifierp(sexp) and var == quantifier_var(sexp):
      return Typ.create(T_ENTITY)
    else:
      for arg in application_args(sexp):
        t = type_in(var, arg)
        if t:
          return t
  return False

def split(sexp, subexp):
  vrz = variables(sexp)
  vrz = [int(var[1:]) for var in vrz]

  #subtyp = typ(subexp)
  subvars = free_variables(subexp)

  #print subexp
  #print subtyp
  #print subvars

  # TODO orderings
  g = subexp
  for var in subvars:
    #t = type_in(var, sexp)
    t = exp_typ_in(sexp, var)
    g = [LAMBDA, var, t, g]

  #print "###"
  #print pretty_lambda(sexp)
  #print pretty_lambda(g)

  #gtyp = typ(g)
  gtyp = exp_typ_in(g, g)
  #print gtyp
  #print

  results = []

  # total substitution
  if g == subexp:
    if vrz:
      nvar = '$%d' % (max(vrz) + 1)
    else:
      nvar = '$0'
    #t = Typ.product([gtyp, typ(sexp)])
    t = gtyp
    replaced = replace_with_variable(sexp, g, nvar)
    results.append((g, [LAMBDA, nvar, t, replaced]))

    #if not Typ.simplep(gtyp):
    #  nexp = [nvar, '?VARIABLE']
    #  rep2 = replace_with_variable(sexp, g, nexp)
    #  print rep2
    #  results.append((g, [LAMBDA, nvar, t, rep2]))

  if subvars:

    # application
    if vrz:
      nvar = '$%d' % (max(vrz) + 1)
    else:
      nvar = '$0'
    napp = [nvar] + sorted(list(subvars)) # TODO only takes one var!
    #print "replacing %s with %s in %s" % (subexp, napp, sexp)
    replaced = replace_with_variable(sexp, subexp, napp)
    #t = Typ.product([gtyp, typ(sexp)])
    t = gtyp
    results.append((g, [LAMBDA, nvar, t, replaced]))
    #print g
    #print t.signatures
    #print [LAMBDA, nvar, t, replaced]
    #print "DID SUBVARS"

    # composition
    if len(subvars) > 1:
      for var in subvars:
        vz = sorted(list(subvars))
        vz.remove(var)
        #vz.insert(0, var)
        napp = [nvar] + vz
        replaced = replace_with_variable(sexp, subexp, napp)
        #g2typ = Typ.return_typ(gtyp)
        #t = Typ.product([g2typ, typ(sexp)])
        t = Typ.return_typ(gtyp)
        results.append((g, [LAMBDA, nvar, t, replaced]))
        #print vz

  #if subvars:
  #  nvar = '$%d' % (max(vrz) + 1)
  #  nvar2 = '$%d' % (max(vrz) + 2)
  #  nexp = [LAMBDA, nvar, '?', 'REPLACED_HERE'] 
  #  replaced = replace_with_variable(sexp, subexp, nexp)
  #  results.append((g, [LAMBDA, nvar2, '?', replaced]))

  #print g
  #gtyp = typ(g)
  #if not Typ.simplep(gtyp):
  #  pass

  for i in range(len(results)):
    results[i] = (normalize_variables(remove_vacuous_lambdas(results[i][0]), {}),
                  normalize_variables(remove_vacuous_lambdas(results[i][1]), {}))

  #print
  return results

  #replaced = replace_with_variable(sexp, subexp, nvar)
  #assert replaced
  ##t = Typ.create((typ(subexp), typ(sexp)))
  #t = Typ.product([typ(subexp), typ(sexp)])
  #return (subexp, [LAMBDA, nvar, str(t), replaced])

def totally_vacuous(sexp):
  if atomp(sexp):
    return varp(sexp)
  if lambdap(sexp):
    return totally_vacuous(lambda_body(sexp))
  if applicationp(sexp):
    return all(totally_vacuous(s) for s in sexp)

def normalize_variables(sexp, vardict):
  #print "NORM", sexp
  if len(vardict) == 0:
    nvar = '$0'
  else:
    vrz = [int(var[1:]) for var in vardict.values()]
    nvar = '$%d' % (max(vrz) + 1)
  if atomp(sexp):
    if varp(sexp):
      #print 'VAR RENAME'
      return vardict[sexp]
    else:
      #print 'ATOM'
      return sexp
  elif lambdap(sexp):
    aname = lambda_arg_name(sexp)
    atyp = lambda_arg_typ(sexp)
    body = lambda_body(sexp)
    vardict[aname] = nvar
    #print 'LAMBDA RENAME'
    return [LAMBDA, nvar, atyp, normalize_variables(body, vardict)]
  elif applicationp(sexp):
    if quantifierp(sexp):
      vardict[quantifier_var(sexp)] = nvar
      q = list(sexp)
      q[1] = nvar
      for i in range(2, len(q)):
        q[i] = normalize_variables(q[i], vardict)
      #print 'QUANT RENAME'
      return q
    else:
      #print 'APPLICATION'
      return [normalize_variables(s, vardict) for s in sexp]
  else:
    assert False

def remove_vacuous_lambdas(sexp):
  #return sexp
  if atomp(sexp):
    return sexp
  elif applicationp(sexp):
    return [remove_vacuous_lambdas(s) for s in sexp]
  elif lambdap(sexp):
    var = lambda_arg_name(sexp)
    t = lambda_arg_typ(sexp)
    fvars = free_variables(lambda_body(sexp))
    if var in fvars:
      return [LAMBDA, var, t, remove_vacuous_lambdas(lambda_body(sexp))]
    else:
      return remove_vacuous_lambdas(lambda_body(sexp))
  else:
    assert False

def pretty_lambda(sexp):
  if atomp(sexp):
    return sexp
  if lambdap(sexp):
    return '(lambda ' + lambda_arg_name(sexp) + ' ' + str(lambda_arg_typ(sexp)) + ' ' + pretty_lambda(lambda_body(sexp)) + ')'
  return '(' + ' '.join([pretty_lambda(s) for s in sexp]) + ')'

#def split(sexp, subexp):
#  #print "split %s, %s" % (sexp, subexp)
#  if sexp == subexp:
#    t = typ(sexp)
#    return [LAMBDA, '$$', "<%s, %s>" % (t, t), '$$']
#  if applicationp(sexp):
#    args = application_args(sexp)
#    if subexp in args:
#      # TODO variable renaming
#      # TODO what about repeated subexps?
#      #print args
#      i = args.index(subexp)
#      #print args[i]
#      args[i] = '$$'
#      #print args
#      nsexp = [application_function(sexp)] + args
#      #print nsexp
#      t = "<%s, %s>" % (typ(subexp), typ(sexp))
#      curried = [LAMBDA, '$$', typ, nsexp]
#      #print curried
#      return curried
#    else:
#      #print "can't do %s, %s" % (sexp, subexp)
#      #assert False
#      for arg in args:
#        sse = subexps(arg)
#        if subexp in 
#      print 
#      # TODO recurse
#  elif lambdap(sexp):
#    # can't replace the body, or variable would be vacuous
#    laname = lambda_arg_name(sexp)
#    latyp = lambda_arg_typ(sexp)
#    lbody = lambda_body(sexp)
#    sp = split(lbody, subexp)
#    return [LAMBDA, laname, latyp, sp]
#  else:
#    assert False

def typ(sexp):
  return exp_typ_in(sexp, sexp)
#def typ(sexp):
#  global __functs__
#  if atomp(sexp):
#    if functp(sexp):
#      return __functs__[sexp]
#    elif varp(sexp):
#      return Typ.create_ambiguous([T_TRUTH, T_ENTITY])
#    else:
#      # TODO allow truth literals
#      return Typ.create(T_ENTITY)
#  elif lambdap(sexp):
#    arg_typ = Typ.create(lambda_arg_typ(sexp))
#    ret_typ = typ(lambda_body(sexp))
#    #b = lambda_body(sexp)
#    #print application_function(b)
#    #print application_args(b)
#    #print applicationp(lambda_body(sexp))
#    #return Typ.create((arg_typ, ret_typ))
#    return Typ.product([arg_typ, ret_typ])
#  elif applicationp(sexp):
#    return application_typ(sexp)
#  else:
#    assert False

def exp_typ_in(exp, se, bindings = None):
  global __functs__
  if bindings == None:
    bindings = {}
  if atomp(exp):
    if se == exp:
      return Typ.create(T_ENTITY) # TODO truth literal?
    else:
      return None
  elif lambdap(exp):
    #t = Typ.create_from_string(lambda_arg_typ(exp))
    t = lambda_arg_typ(exp)
    if isinstance(t,str):
      t = Typ.create(t)
    if se == lambda_arg_name(exp):
      return t
    elif se == exp:
      bindings[lambda_arg_name(exp)] = t
      #return Typ.product([t, exp_typ_in(lambda_body(exp), lambda_body(exp),
        #bindings)])
      r = exp_typ_in(lambda_body(exp), lambda_body(exp), bindings)
      return Typ.product([t,r])
    else:
      bindings[lambda_arg_name(exp)] = t
      return exp_typ_in(lambda_body(exp), se, bindings)
  elif quantifierp(exp):
    #t = __functs__[application_function(exp)][0]
    t = Typ.create(T_ENTITY) # TODO doesn't need to be manual
    if se == quantifier_var(exp):
      return t
    elif se == exp:
      return Typ.return_typ(__functs__[application_function(exp)])
    else:
      bindings[quantifier_var(exp)] = t
      for i in range(2, 2+len(quantifier_args(exp))):
        r = exp_typ_in(exp[i], se, bindings)
        if not (r == None):
          return r
      return None
  elif applicationp(exp):
    if se == exp:
      if application_function(exp) in bindings:
        return Typ.return_typ(bindings[application_function(exp)])
      else:
        return Typ.return_typ(__functs__[application_function(exp)])
    else:
      for i in range(1, 1 + len(application_args(exp))):
        r = exp_typ_in(exp[i], se, bindings)
        if not (r == None):
          return r
      #print "couldn't get %s from %s" % (se, exp)
      #assert False
      return None

def application_typ(sexp):

  #print sexp

  funct_typ = typ(application_function(sexp))
  # the arg signature might be any combination of the signatures of each arg
  arg_typ = Typ.product([typ(arg) for arg in application_args(sexp)])

  #assert functp(application_function(sexp))

  funct_arg_typ = Typ.arg_typ(funct_typ)
  funct_return_typ = Typ.return_typ(funct_typ)

  print sexp
  print "function expects", funct_arg_typ
  print "actual args", application_args(sexp)
  print "arg_typ", arg_typ

  #assert Typ.check_equivalence(arg_typ, funct_arg_typ)
  # TODO doesn't handle functions properly
  return funct_return_typ

# def annotated_type(atom):
#   global __types__
#   assert atomp(atom)
#   colon_loc = atom.index(':')
#   assert colon_loc >= 0
#   typ = atom[colon_loc+1:]
#   return base_typ(typ)

def application_function(sexp):
  assert applicationp(sexp)
  return sexp[0]

def application_args(sexp):
  assert applicationp(sexp)
  return sexp[1:]

def quantifier_var(sexp):
  assert quantifierp(sexp)
  return sexp[1]

def quantifier_args(sexp):
  assert quantifierp(sexp)
  return sexp[2:]

def lambda_arg_name(sexp):
  return sexp[1]

def lambda_arg_typ(sexp):
  return sexp[2]

def lambda_body(sexp):
  assert len(sexp) == 4
  return sexp[3]

def base_typ(typ):
  if typ in (T_TRUTH, T_INT):
    return typ
  return T_ENTITY

#def same_typ(t1, t2):
#  if isinstance(t1, list) and len(t1) == 1:
#    t1 = t1[0]
#  if isinstance(t2, list) and len(t2) == 1:
#    t2 = t2[0]
#  return t1 == t2

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
  test_split()

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
  EXPECT_TRUE(Typ.check_equivalence(Typ.create(T_ENTITY), typ(s1)))

  s2 = ['lambda', '$0', 'e', ['and', ['state:t', '$0'], ['exists', '$1', ['and', ['state:t', '$1'], ['loc:t', 'mississippi_river:r', '$1'], ['next_to:t', '$0', '$1']]]]]
  EXPECT_TRUE(Typ.check_equivalence(Typ.create((T_ENTITY, T_TRUTH)), typ(s2)))
  
  s3 = ['argmin', '$0', ['city:t', '$0'], ['population:i', '$0']]
  EXPECT_TRUE(Typ.check_equivalence(Typ.create(T_ENTITY), typ(s3)))

  s4 = 'equals:t'
  EXPECT_TRUE(Typ.check_equivalence(Typ.create((T_ENTITY, T_ENTITY, T_TRUTH)), typ(s4)))

  #s5 = ['city:t', ['equals:t', 'thing1:c', 'thing2:c']]
  #try:
  #  typ(s5)
  #except AssertionError:
  #  EXPECT_TRUE(True)
  #else:
  #  EXPECT_TRUE(False)

def test_split():
  #s3 = ['argmin', '$0', ['city:t', '$0'], ['population:i', '$0']]
  #s3 = ['lambda', '$0', 'e', ['and', ['state:t', '$0'], ['exists', '$1', ['and', ['state:t', '$1'], ['loc:t', 'mississippi_river:r', '$1'], ['next_to:t', '$0', '$1']]]]]
  #s3 = ['lambda', '$0', 'e', ['and', ['state:t', '$0'], ['next_to:t', '$0', 'texas:s']]]
  s3 = ['lambda', '$1', 'e', ['lambda', '$0', 'e', ['and', ['state:t', '$0'], ['next_to:t', '$0', '$1']]]]
  print "s: %s\n" % s3
  subs = subexps(s3)
  print '\n'.join([str(sub) for sub in subs])
  print
  splits = [split(s3, sub) for sub in subs]
  #print '\n'.join(['%s : %s' % (pretty_lambda(sp[0]), pretty_lambda(sp[1])) for sp in splits])
  for sps in splits:
    for sp in sps:
      print pretty_lambda(sp[0])
      print pretty_lambda(sp[1])
      print
    print
  print
  #print
  #print
  #print "splits: %s" % splits
  #print
  #s2 = ['lambda', '$0', 'e', ['and', ['state:t', '$0'], ['exists', '$1', ['and', ['state:t', '$1'], ['loc:t', 'mississippi_river:r', '$1'], ['next_to:t', '$0', '$1']]]]]
  #print "s: %s" % s2
  #subs = subexps(s2)
  #print "subs: %s" % subs
  #splits = [split(s2, sub) for sub in subs]
  #print "splits: %s" % splits
