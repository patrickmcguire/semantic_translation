import random

class Typ:

  def __init__(self):
    pass

  @staticmethod
  def create_from_string(desc):
    return create('?')

  @staticmethod
  def create(signature):
    #print 'CREATE CALLED', signature
    if isinstance(signature, Typ):
      return signature
    t = Typ()
    t.signatures = set()
    t.signatures.add(signature)
    return t

  @staticmethod
  def create_ambiguous(signatures):
    t = Typ()
    t.signatures = set(signatures)
    return t

  @staticmethod
  def ambiguousp(t):
    return len(t.signatures)

  @staticmethod
  def check_equivalence(t1, t2):
    #return True # TODO TODO TODO
    tt = Typ.create_ambiguous([typ for typ in t1.signatures if typ in t2.signatures])
    if len(tt.signatures) == 0:
      return None
    return tt

  @staticmethod
  def arg_typ(t):
    return Typ.create_ambiguous([tt[:-1] for tt in t.signatures])

  @staticmethod
  def return_typ(t):
    return Typ.create_ambiguous([tt[-1] for tt in t.signatures])

  @staticmethod
  def product(typs):
    lists = [typ.signatures for typ in typs]
    result = [()]
    for l in lists:
      result = [rl + (nl,) for nl in l for rl in result]
    return Typ.create_ambiguous(result)

  def __str__(self):
    #return "Typ(%s)" % list(self.signatures)
    #sig = random.sample(self.signatures, 1)[0]
    sig = sorted(list(self.signatures))[0]
    return self.__str_helper__(sig)[:-1] #+ (' (%d)' % len(self.signatures))

  def __str_helper__(self, sig):
    if isinstance(sig, str):
      return sig + ','
    else:
      return '<' + ''.join([self.__str_helper__(ssig) for ssig in sig])[:-1] + '>,'

  def __repr__(self):
    return self.__str__()

  @staticmethod
  def simplep(typ):
    return all([len(t) == 1 for t in typ.signatures])
