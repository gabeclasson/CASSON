from abc import abstractmethod
import math
from functools import reduce
from typing import OrderedDict

default_bindings = {
        "Pi": math.pi,
        "E": math.e
    }

class Node:
    symbol = None
    name = "Node"

    def __init__(self, children):
        self.children = children

    def __repr__(self):
        return f"{self.name}([{', '.join(map(repr, self.children))}])"

    def __str__(self):
        return f"{self.symbol}({', '.join(map(str,self.children))})"

    def __eq__(self, other):
        return self.symbol == other.symbol and self.children == other.children        

    def simplify(self):
        return type(self)([child.simplify() for child in self.children])

class Function(Node):
    symbol = None
    name = "Function"

    def __init__(self, children):
        assert len(children) >= self.min_args and len(children) <= self.max_args, f"{self.symbol} expected between {self.min_args} and {self.max_args} arguments."

        super().__init__(children)

    @abstractmethod
    def evaluate(self, bindings={}):
        pass

    @abstractmethod
    def derivative(self, symbol):
        pass

    def simplify(self):
        self = super().simplify()
        if all([isinstance(child, Number) and isinstance(child.symbol, float) for child in self.children]):
            return Number(self.evaluate())
        return self

class UnaryFunction(Function):
    symbol = None
    name = "UnaryFunction"
    min_args = 1
    max_args = 1

class Operator(Function):
    precedence = 0
    is_left_associative = True
    is_right_associative = False

class PrefixOperator(Operator):
    min_args = 1
    max_args = 1
    precedence = 0
    is_left_associative = True
    is_right_associative = False

    def __str__(self):
        child = self.children[0]
        if isinstance(child, Operator) and self.precedence > child.precedence:
            return f"{self.symbol}({str(child)})"
        return f"{self.symbol}{str(child)}"

class BinaryOperator(Operator):
    min_args = 2
    max_args = 2
    is_left_associative = True
    is_right_associative = True
    precedence = 0
    str_spacing = ""

    def __str__(self):
        left = self.children[0]
        right = self.children[1]
        left_str = str(left)
        right_str = str(right)
        if issubclass(type(left), Operator) and (left.precedence < self.precedence or (left.precedence == self.precedence and not self.is_left_associative)):
            left_str = "(" + left_str + ")"
        if issubclass(type(right), Operator) and (right.precedence < self.precedence or (right.precedence == self.precedence and not self.is_right_associative)):
            right_str = "(" + right_str + ")"
        return f"{left_str}{self.str_spacing}{self.symbol}{self.str_spacing}{right_str}"

class Leaf(Node):
    name = "Leaf"

    def __init__(self, symbol):
        self.symbol = symbol
        super().__init__([])
    
    def __repr__(self):
        return f"{self.name}({repr(self.symbol)})"

    def __str__(self):
        return str(self.symbol)

    def simplify(self):
        return self

class Variable(Leaf):
    name = "Variable"
    
    def evaluate(self, bindings={}):
        bindings = bindings | default_bindings
        assert self.symbol in bindings, "Cannot evaluate unbound variable"
        if self.symbol in bindings:
            return bindings[self.symbol]

    def derivative(self, symbol):
        if self.symbol == symbol:
            return NUMBER_1
        return NUMBER_0

class Number(Leaf):
    name = "Number"
    
    def evaluate(self, bindings={}):
        return self.symbol
    
    def derivative(self, symbol):
        return NUMBER_0

class Add(BinaryOperator):
    symbol = "+"
    name = "Add"
    precedence = 1
    str_spacing = " "

    def evaluate(self, bindings={}):
        x, y = self.children
        return x.evaluate(bindings) + y.evaluate(bindings)

    def derivative(self, symbol):
        x, y = self.children
        return Add([x.derivative(symbol), y.derivative(symbol)]).simplify()

    def simplify(self):
        self = super().simplify()
        if isinstance(self, Number):
            return self

        x, y = self.children

        # Identity
        if x == NUMBER_0: 
            return y
        elif y == NUMBER_0:
            return x

        return self

class Multiply(BinaryOperator):
    symbol = "*"
    name = "Multiply"
    precedence = 2

    def evaluate(self, bindings={}):
        x, y = self.children
        return x.evaluate(bindings) * y.evaluate(bindings)

    def derivative(self, symbol):
        x, y = self.children
        return Add([Multiply([x.derivative(symbol), y]), Multiply([y.derivative(symbol), x])]).simplify()

    def simplify(self):
        self = super().simplify()
        if isinstance(self, Number):
            return self
        x, y = self.children
        # Zero product
        if x == NUMBER_0 or y == NUMBER_0:
            return NUMBER_0
        # Identity
        if x == NUMBER_1: 
            return y
        elif y == NUMBER_1:
            return x
        # Negation

        return self

class Subtract(BinaryOperator):
    symbol = "-"
    name = "Subtract"
    precedence = 1
    is_right_associative = False
    str_spacing = " "

    def evaluate(self, bindings={}):
        x, y = self.children
        return x.evaluate(bindings) - y.evaluate(bindings)

    def derivative(self, symbol):
        x, y = self.children
        return Subtract([Multiply([x.derivative(symbol), y]), Multiply([y.derivative(symbol), x])]).simplify()

    def simplify(self):
        self = super().simplify()
        if isinstance(self, Number):
            return self

        x, y = self.children

        # Identity
        if x == NUMBER_0: 
            return Negate([y])
        elif y == NUMBER_0:
            return x

        return self

class Divide(BinaryOperator):
    symbol = "/"
    name = "Divide"
    precedence = 2
    is_right_associative = False

    def evaluate(self, bindings={}):
        x, y = self.children
        return x.evaluate(bindings) / y.evaluate(bindings)

    def derivative(self, symbol):
        x, y = self.children
        return Divide([Subtract([Multiply([x.derivative(symbol), y]), Multiply([y.derivative(symbol), x])]), Power([y, NUMBER_2])]).simplify()

    def simplify(self):
        self = super().simplify()
        if isinstance(self, Number):
            return self
        x, y = self.children
        # Zero product
        if x == NUMBER_0:
            return NUMBER_0
        # Identity
        if y == NUMBER_1:
            return x
        if x == y:
            return NUMBER_1
        return self

class Power(BinaryOperator):
    name = "Power"
    symbol = "^"
    is_left_associative = False
    precedence = 3
    
    def evaluate(self, bindings={}):
        a, b = self.children
        return pow(a.evaluate(bindings), b.evaluate(bindings))

    def derivative(self, symbol):
        z, y = self.children
        return Multiply([self, Add([Multiply([y.derivative(symbol), Ln([z])]), Divide([Multiply([z.derivative(symbol), y]), z])])]).simplify()

    def simplify(self):
        self = super().simplify()
        if isinstance(self, Number):
            return self
        x, y = self.children
        
        if x == NUMBER_0 and y != NUMBER_0:
            return NUMBER_0
        if y == NUMBER_0 and x != NUMBER_0:
            return NUMBER_1
        if x == NUMBER_1:
            return NUMBER_1
        if y == NUMBER_1:
            return x
        return self

class Ln(UnaryFunction):
    symbol = "ln"
    name = "Ln"

    def evaluate(self, bindings={}):
        return math.log(self.children[0].evaluate(bindings))

    def derivative(self, symbol):
        x = self.children[0]
        return Divide([x.derivative(symbol), x]).simplify()

    def simplify(self):
        self = super().simplify()
        if isinstance(self, Number):
            return self
        x = self.children[0]
        
        if x == NUMBER_1:
            return NUMBER_0
        if x == Variable("E"):
            return NUMBER_1
        return self

class Sine(UnaryFunction):
    symbol = "sin"
    name = "Sine"

    def evaluate(self, bindings={}):
        return math.sin(self.children[0].evaluate(bindings))

    def derivative(self, symbol):
        return Multiply([Cosine(self.children), self.children[0].derivative(symbol)]).simplify()

class Cosine(UnaryFunction):
    symbol = "cos"
    name = "Cosine"

    def evaluate(self, bindings={}):
        return math.cos(self.children[0].evaluate(bindings))

    def derivative(self, symbol):
        return Multiply([Negate([Sine(self.children)]), self.children[0].derivative(symbol)]).simplify()

class Tangent(UnaryFunction):
    symbol = "tan"
    name = "Tangent"

    def evaluate(self, bindings={}):
        return math.tan(self.children[0].evaluate(bindings))

    def derivative(self, symbol):
        x = self.children[0]
        return Multiply([Power([Secant([x]), NUMBER_2]), x.derivative(symbol)]).simplify()

class Secant(UnaryFunction):
    symbol = "sec"
    name = "Secant"

    def evaluate(self, bindings={}):
        return 1/math.cos(self.children[0].evaluate(bindings))

    def derivative(self, symbol):
        x = self.children[0]
        return Multiply([Multiply([Secant([x]), Tangent([x])]), x.derivative(symbol)]).simplify()

class Cotangent(UnaryFunction):
    symbol = "cot"
    name = "Cotangent"

    def evaluate(self, bindings={}):
        return 1/math.tan(self.children[0].evaluate(bindings))

    def derivative(self, symbol):
        x = self.children[0]
        return Multiply([Negate([Power([Cosecant([x]), NUMBER_2])]), x.derivative(symbol)]).simplify()

class Cosecant(UnaryFunction):
    symbol = "csc"
    name = "Cosecant"

    def evaluate(self, bindings={}):
        return 1/math.sin(self.children[0].evaluate(bindings))

    def derivative(self, symbol):
        x = self.children[0]
        return Multiply([Multiply([Negate([Cosecant([x])]), Cotangent([x])]), x.derivative(symbol)]).simplify()

class Sqrt(UnaryFunction):
    symbol = "sqrt"
    name = "Sqrt"

    def evaluate(self, bindings={}):
        return math.sqrt(self.children[0].evaluate(bindings))

    def derivative(self, symbol):
        x = self.children[0]
        return Multiply([Divide([NUMBER_1, Multiply([NUMBER_2, Sqrt([x])])]), x.derivative(symbol)]).simplify()

class Abs(UnaryFunction):
    symbol = "abs"
    name = "Abs"

    def evaluate(self, bindings={}):
        return math.abs(self.children[0].evaluate(bindings))

    def derivative(self, symbol):
        x = self.children[0]
        return Multiply([Sign([x]), x.derivative(symbol)]).simplify()

class Sign(UnaryFunction):
    symbol = "sign"
    name = "Sign"

    def evaluate(self, bindings={}):
        inside = self.children[0].evaluate(bindings)
        if inside > 0:
            return 1
        elif inside < 0:
            return -1
        else:
            return 0

    def derivative(self, symbol):
        return NUMBER_0

class Arcsin(UnaryFunction):
    symbol = "arcsin"
    name = "Arcsin"

    def evaluate(self, bindings={}):
        return math.asin(self.children[0].evaluate(bindings))

    def derivative(self, symbol):
        x = self.children[0]
        return Multiply([Divide([NUMBER_1, Sqrt([Subtract([NUMBER_1, Power([x, NUMBER_2])])])]), x.derivative(symbol)]).simplify()

class Negate(PrefixOperator):
    symbol = "-"
    name = "Negate"
    precedence = 2.5

    def evaluate(self, bindings={}):
        return -1 * self.children[0].evaluate(bindings)

    def derivative(self, symbol):
        return Negate([self.children[0].derivative(symbol)]).simplify()

    def simplify(self):
        self = super().simplify()
        if isinstance(self, Number):
            return self
        x = self.children[0]
        if isinstance(x, Negate):
            return x.children[0]
        if x == NUMBER_0:
            return x
        return self

binary_operators = [Add, Subtract, Multiply, Divide, Power]
binary_operators_dict = {Operator.symbol: Operator for Operator in binary_operators} 

unary_functions = [Sine, Cosine, Ln, Secant, Tangent, Cosecant, Cotangent, Sqrt, Arcsin, Sign, Abs]
unary_functions_dict = {Operator.symbol: Operator for Operator in unary_functions} 

prefix_operators = [Negate]
prefix_operators_dict = {Operator.symbol: Operator for Operator in prefix_operators} 


NUMBER_0 = Number(0)
NUMBER_1 = Number(1)
NUMBER_2 = Number(2)
E = Variable("E")
PI = Variable("Pi")