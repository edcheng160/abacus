# Exercise blah 1: Viewing and Establishing the Status of a File
# blah blah blah
# commit #2
# commit #3

class Compute:
  def __init__(self, operands):
    self.operands = operands

  def exponent(self):
    num_exponent = self.operands[0] ** self.operands[1]
    print(num_exponent)

  def add(self):
    total = 0
    for item in self.operands:
        total += item
    print(total)

  def subtract(self):
    if self.operands is None:
        return
    difference = self.operands[0]
    for i in range(1, len(self.operands)):
        difference -= self.operands[i]
    print(difference)

  def divide(self):
      if self.operands is None:
          return
      quotient = self.operands[0]
      for i in range(1, len(self.operands)):
          quotient /= self.operands[i]
      print(quotient)    
    
  def multiply(self):
    if self.operands is None:
        return
    product = 1
    for item in self.operands:
        product *= item
    print(product)

  def power(self):
      res = self.operands[0] ** self.operands[1]
      print(res)
