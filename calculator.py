def calculator(op, a, b):
    match op:
        case "add":
            return a + b
        case "subtract":
            return a - b
        case "multiply":
            return a * b
        case "divide":
            if b == 0:
                return "Error: Division by zero"
            return a / b
        case _:
            return "Invalid operation"

def main():
    print("Simple Calculator")
    print("Operations: add, subtract, multiply, divide")

    op = input("Enter operation: ").strip().lower()
    try:
    	a = float(input("Enter first number: "))
    	b = float(input("Enter second number: "))
    except:
    	printf("Error:Enter a valid number")
	return

    result = calculator(op, a, b)
    print(f"Result: {result}")

if __name__ == "__main__":
    main()
