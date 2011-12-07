import sys
import inspect

# TODO decorated

def EXPECT_EQ(expected, val):
  calling_frame = inspect.stack()[2]
  print 'TEST IN',
  print inspect.getmodule(calling_frame[0]).__name__,
  print ':',
  print calling_frame[3],
  if not expected == val:
    err = "FAILED. Expected %s, got %s" % (expected, val)
    raise Exception(err)
    print err
  else:
    print "PASSED."

def EXPECT_TRUE(val):
  if val:
    return EXPECT_EQ(val, val)
  else:
    return EXPECT_EQ(True, val)

def EXPECT_FALSE(val):
  if not val:
    return EXPECT_EQ(val, val)
  else:
    return EXPECT_EQ(True, val)
