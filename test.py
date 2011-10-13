import sys

def EXPECT_EQ(expected, val):
  if not expected == val:
    err = "TEST FAILED. Expected %s, got %s" % (expected, val)
    raise Exception(err)
  else:
    pass
    #print >>sys.stderr, "TEST PASSED."

def EXPECT_TRUE(val):
  return EXPECT_EQ(True, val)

def EXPECT_FALSE(val):
  return EXPECT_EQ(False, val)

