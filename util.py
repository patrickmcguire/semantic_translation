import re
from test import *

def read_tokens(exp):
  return read_tokens_inner(re.sub(r'(?<=\()|\s|(?=\))', '\f', exp).split('\f'))

def read_tokens_inner(exp_tokens):
  assert exp_tokens[0] == '('
  assert exp_tokens[-1] == ')'
  exp = []
  i = 1
  while i < len(exp_tokens) - 1:
    tok = exp_tokens[i]
    assert tok != ')'
    if tok == '(':
      ii = index_after_matching(exp_tokens, i)
      exp.append(read_tokens_inner(exp_tokens[i:ii]))
      i = ii
    else:
      exp.append(exp_tokens[i])
      i += 1
  return exp

def sexp_begin(str):
  return str[0] == '('

def sexp_end(str):
  return str[-1] == ')'

def index_after_matching(tokens, i):
  assert tokens[i] == '('
  stack = 1
  while i < len(tokens):
    i += 1
    if tokens[i] == '(': stack += 1
    if tokens[i] == ')': stack -= 1
    if stack < 0:
      raise Exception('index_after_matching: no matching paren!')
    if stack == 0: return i + 1

###

def test():
  test_sexp_begin()
  test_sexp_end()
  test_read_tokens_flat()
  test_read_tokens_nested()
  test_read_tokens_malformed()

def test_sexp_begin():
  EXPECT_TRUE(sexp_begin('(a'))
  EXPECT_FALSE(sexp_begin('b)'))
  EXPECT_FALSE(sexp_begin('c'))

def test_sexp_end():
  EXPECT_FALSE(sexp_end('(a'))
  EXPECT_TRUE(sexp_end('b)'))
  EXPECT_FALSE(sexp_end('c'))

def test_read_tokens_flat():
  q = '(capital:c maine:s)'
  ans = ['capital:c', 'maine:s']
  EXPECT_EQ(ans, read_tokens(q))

def test_read_tokens_nested():
  q = '(lambda $0 e (and (state:t $0) (exists $1 (and (state:t $1) (loc:t mississippi_river:r $1) (next_to:t $0 $1)))))'
  ans = ['lambda', '$0', 'e', ['and', ['state:t', '$0'], ['exists', '$1', ['and', ['state:t', '$1'], ['loc:t', 'mississippi_river:r', '$1'], ['next_to:t', '$0', '$1']]]]]
  EXPECT_EQ(ans, read_tokens(q))

def test_read_tokens_malformed():
  pass
