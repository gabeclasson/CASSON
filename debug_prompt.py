from syntax_parser import *

string = ""
while True:
    string = input("> ")
    if string == "exit()":
        break
    tokenized = tokenize(string)
    print("tok >>", tokenized)
    parsed = parse(tokenized)
    print("prs >>", repr(parsed))
    stringified = str(parsed)
    print("str >>", stringified)
    simplified = parsed.simplify()
    print("smp >>", simplified)
    derivative = parsed.derivative("x")
    print("ddx >>", derivative)