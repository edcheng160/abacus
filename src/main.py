import lib.compute as comp

def main():
    obj = comp.Compute('+', [9.0,3.0,2.0])
    obj.add()
    obj.multiply()
    obj.subtract()
    obj.divide()

if __name__ == "__main__":
    main()    
