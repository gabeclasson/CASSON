from syntax_parser import *

string = ""
while True:
    string = input("ddx> ")
    if string == "exit()":
        break
    tokenized = tokenize(string)
    parsed = parse(tokenized)
    if parsed is not None:
        derivative = parsed.derivative("x")
        print(">>>", derivative)

