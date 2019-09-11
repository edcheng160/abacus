# Exercise 1: Viewing and Establishing the Status of a File

class Compute:
  def __init__(self, operator, operands):
    self.operator = operator
    self.operands = operands

  def add(self):
    total = 0
    for item in self.operands:
        total =+ item
        print(total)

  def subtract(self):
    pass

  def divide(self):
    pass
    
  def multiply(self):
    sum = 1
    for item in self.operands:
        sum *= item
    print(sum)
