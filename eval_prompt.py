from syntax_parser import *

string = ""
while True:
    string = input("evl> ")
    if string == "exit()":
        break
    tokenized = tokenize(string)
    parsed = parse(tokenized)
    if parsed is not None:
        evaluated = parsed.evaluate()
        print(">>>", evaluated)

