import lib.compute as comp
import lib.investment as inv

def main():
    obj = comp.Compute([9.0,3.0,2.0])
    obj.add()
    obj.multiply()
    obj.subtract()
    obj.divide()
    obj.power()

    model = inv.InvestmentModel(1000.0)
    model.print_model()

if __name__ == "__main__":
    main()
