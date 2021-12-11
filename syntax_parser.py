import re, inspect
from function import *

NUMBER_REGEXP = r"\d+(?:\.\d*)?|\.\d+"
BINARY_OPERATOR_REGEXP = r"[\(\)\+\-\/\*\^]"
PREFIX_OPERATOR_REGEXP = r"[\-]"
NAME_REGEXP = r"[A-Za-z]+"

def tokenize(string): 
    return re.findall(r'(?:' + BINARY_OPERATOR_REGEXP + r')|(?:' + NUMBER_REGEXP + r')|(?:' + NAME_REGEXP + r')|(?:' + PREFIX_OPERATOR_REGEXP + ")", string)

def parse(tokens):
    previous, index = None, 0
    while index < len(tokens):
        previous, index = parse_partial(tokens, index, Operator, previous)
    return previous

"""
Parses tokens beginning at index. It will parses to the right 
until it reaches a binary operator of higher precedence than 
the limiting operator, at which point it will return the index. 
"""
def parse_partial(tokens, index, limiting_operator, previous): 
    new_index, token = index, tokens[index]
    # Subexpression parsing
    if token == "(":
        parsed, new_index = parse_partial(tokens, index + 1, Operator, None)
        assert new_index < len(tokens) and tokens[new_index] == ")", "Mismatched parentheses"
    # Primitive parsing
    else: 
        parsed = parse_primitive(token, previous is not None)
    new_index += 1
    # If the primitive is a Function class, we construct the function node and
    # parse relevant subexpressions
    if inspect.isclass(parsed) and issubclass(parsed, Function): 
        # Unary function
        if issubclass(parsed, UnaryFunction):
            assert new_index < len(tokens) and tokens[new_index] == "(", \
                "Unary function calls require parentheses"
            argument, new_index = parse_partial(tokens, new_index + 1, Operator, None)
            assert new_index < len(tokens) and tokens[new_index] == ")", \
                "Mismatched parentheses in unary function call"
            new_index += 1
            parsed = parsed([argument])
        # Prefix operator
        elif issubclass(parsed, PrefixOperator):
            argument, new_index = parse_partial(tokens, new_index, parsed, None)
            parsed = parsed([argument])
        # Binary operator
        elif issubclass(parsed, BinaryOperator):
            assert previous, "Binary operator missing first argument"
            next_parsed, new_index = parse_partial(tokens, new_index, parsed, previous)
            parsed = parsed([previous, next_parsed])
    # Now that parsed contains the processed, current node, we must look to 
    # the next token to determine whether to return the current node or 
    # continue parsing to the right. This is based on operator precedence.
    if new_index < len(tokens) and tokens[new_index] != ")": 
        if tokens[new_index] != "(":
            next_operator = parse_primitive(tokens[new_index], True)
        else: 
            next_operator = None
        # Implicit multiplication: two adjacent nodes multiply
        if not next_operator or not inspect.isclass(next_operator) \
            or not issubclass(next_operator, BinaryOperator):
            tokens.insert(new_index, "*")
            next_operator = Multiply
        # Operator precedence
        if next_operator.precedence > limiting_operator.precedence or (
            next_operator.is_right_associative and not next_operator.is_left_associative 
            and next_operator.precedence == limiting_operator.precedence):
            return parse_partial(tokens, new_index, limiting_operator, parsed)
    return parsed, new_index

def parse_primitive(token, has_previous):
    if re.match(NUMBER_REGEXP, token):
        try:
            return Number(int(token))
        except:
            return Number(float(token))
    if not has_previous:
        if re.match(PREFIX_OPERATOR_REGEXP, token) and token in prefix_operators_dict:
            return prefix_operators_dict[token]
    if re.match(BINARY_OPERATOR_REGEXP, token) and token in binary_operators_dict:
        return binary_operators_dict[token]
    if has_previous:
        if re.match(PREFIX_OPERATOR_REGEXP, token) and token in prefix_operators_dict:
            return prefix_operators_dict[token]
    if re.match(NAME_REGEXP, token):
        if token in unary_functions_dict:
            return unary_functions_dict[token]
        return Variable(token)
    raise SyntaxError

#parse(tokenize("E^(3x^2 - 42)"))