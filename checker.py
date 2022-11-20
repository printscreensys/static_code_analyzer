import os
import re
import ast

#TODO implement all of the standard PEP8 checks;
#TODO display column numbers;
#TODO disable some of the checks via command-line arguments.
#TODO implement class- and functions- names checking via ast


class Checker:
    MESSAGE_CODES = {
        "S001": "Too long",
        "S002": "Indentation is not a multiple of four",
        "S003": "Unnecessary semicolon after a statement (note that semicolons are acceptable in comments)",
        "S004": "Less than two spaces before inline comments",
        "S005": "TODO found (in comments only and case-insensitive)",
        "S006": "More than two blank lines preceding a code line (applies to the first non-empty line)",
        "S007": "Too many spaces after {}",
        "S008": "Class name {} should be written in CamelCase",
        "S009": "Function name {} should be written in snake_case",
        "S010": "Argument name {} should be written in snake_case",
        "S011": "Variable {} should be written in snake_case",
        "S012": "The default argument value is mutable"
    }

    @staticmethod
    def check_length(line: str) -> bool:
        return len(line) > 79

    @staticmethod
    def check_indentation(line: str) -> bool:
        t = 0
        for c in line:
            if c == " ":
                t += 1
            else:
                break

        return t % 4 != 0

    @staticmethod
    def check_semicolons(line: str) -> bool:
        code = line.split("#")[0]
        if len(code) > 0:
            return code.strip()[-1] == ';'

    @staticmethod
    def check_inline_comments(line: str) -> bool:
        return "  #" not in line and "#" in line and line[0] != "#"

    @staticmethod
    def check_todos(line: str) -> bool:
        line = line.casefold()
        return any(("#todo" in line, "# todo" in line))

    @staticmethod
    def check_blank_lines(lines: list, i: int) -> bool:
        if i > 2:
            return lines[i - 3: i] == ["", "", ""] and lines[i] != ""

    @staticmethod
    def check_spaces(line: str) -> bool:
        return re.match(r"\b(class|def)( {2,})[\w]+[\(\)\:]*", line.strip()) is not None

    @staticmethod
    def check_class_name(line: str) -> bool:
        class_pattern = "[A-Z][a-z]*([A-Z][a-z]*)*"
        return re.match("class( {1,})" + class_pattern + "(\(" + class_pattern + "(,( )?" + class_pattern + ")?\))?\:",
                        line) is None \
               and line.startswith("class")

    @staticmethod
    def check_function_name(line: str) -> bool:
        line = line.strip()
        return re.match(r"def( {1,})(_{0,2})?[a-z][a-z0-9]*(_[a-z]*)*(_{0,2})?\([a-zA-Z\,0-9\[\]\= ]*\)\:",
                        line) is None \
               and line.startswith('def')

    @staticmethod
    def check_argument_name(objects: dict) -> set:
        functions = objects[ast.FunctionDef]
        warnings = set()
        for f in functions:
            for a in f.args.args:
                if re.match("(_{,2})?[a-z]+(_[a-z]*)*(_{,2})?", a.arg) is None:
                    warnings.add(a.arg)

        return warnings

    @staticmethod
    def check_variable_name(objects: dict) -> set:
        variables = objects[ast.Name]
        warnings = set()
        for v in variables:
            if isinstance(v.ctx, ast.Store):
                if re.match("(_{,2})?[a-z]+(_[a-z]*)*(_{,2})?", v.id) is None:
                    warnings.add(v.id)

        return warnings

    @staticmethod
    def check_mutable_value(objects: dict) -> set:
        functions = objects[ast.FunctionDef]
        warnings = set()
        for f in functions:
            for def_arg in f.args.defaults:
                if type(def_arg) in (ast.List, ast.Set, ast.Dict):
                    warnings.add(f.name)
                elif type(def_arg) == ast.Call:
                    if def_arg.func.id in ('set', 'list', 'dict'):
                        warnings.add(f)

        return warnings

    @staticmethod
    def ast_processing(f) -> dict:
        objects = {ast.FunctionDef: [],
                   ast.Name: []}
        tree = ast.parse(f.read())
        nodes = ast.walk(tree)

        for n in nodes:
            if isinstance(n, ast.FunctionDef):
                objects[ast.FunctionDef].append(n)
            if isinstance(n, ast.Name):
                objects[ast.Name].append(n)

        return objects

    @staticmethod
    def test(path, file=None):
        if file:
            path = os.path.join(path, file)
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            lines = list(map(lambda x: x.rstrip(), lines))
            f.seek(0)
            objects = Checker.ast_processing(f)
            checked_args = list(Checker.check_argument_name(objects))
            checked_variables = list(Checker.check_variable_name(objects))
            checked_default_variables = list(Checker.check_mutable_value(objects))

            for i in range(len(lines)):
                if Checker.check_length(lines[i]):
                    print(f"{path}: Line {i + 1}: S001 {Checker.MESSAGE_CODES['S001']}")
                if Checker.check_indentation(lines[i]):
                    print(f"{path}: Line {i + 1}: S002 {Checker.MESSAGE_CODES['S002']}")
                if Checker.check_semicolons(lines[i]):
                    print(f"{path}: Line {i + 1}: S003 {Checker.MESSAGE_CODES['S003']}")
                if Checker.check_inline_comments(lines[i]):
                    print(f"{path}: Line {i + 1}: S004 {Checker.MESSAGE_CODES['S004']}")
                if Checker.check_todos(lines[i]):
                    print(f"{path}: Line {i + 1}: S005 {Checker.MESSAGE_CODES['S005']}")
                if Checker.check_blank_lines(lines, i):
                    print(f"{path}: Line {i + 1}: S006 {Checker.MESSAGE_CODES['S006']}")
                if Checker.check_spaces(lines[i]):
                    constructor = "'class'" if lines[i].startswith("class") else "'def'"
                    print(f"{path}: Line {i + 1}: S007 {Checker.MESSAGE_CODES['S007'].format(constructor)}")
                if Checker.check_class_name(lines[i]):
                    class_name = re.split(" +", lines[i])[1]
                    class_name = re.sub(r'\W+', '', class_name)
                    print(f"{path}: Line {i + 1}: S008 {Checker.MESSAGE_CODES['S008'].format(class_name)}")
                if Checker.check_function_name(lines[i]):
                    function_name = re.split(" +", lines[i])[1]
                    function_name = re.sub(r'\W+', '', function_name)
                    print(f"{path}: Line {i + 1}: S009 {Checker.MESSAGE_CODES['S009'].format(function_name)}")
                j = 0
                while j < len(checked_args):
                    if checked_args[j] in lines[i]:
                        print(f"{path}: Line {i + 1}: S010 {Checker.MESSAGE_CODES['S010'].format(checked_args[j])}")
                        checked_args.remove(checked_args[j])
                    else:
                        j += 1
                j = 0
                while j < len(checked_variables):
                    if checked_variables[j] in lines[i]:
                        print(f"{path}: Line {i + 1}: S011 "
                              f"{Checker.MESSAGE_CODES['S011'].format(checked_variables[j])}")
                        checked_variables.remove(checked_variables[j])
                    else:
                        j += 1
                j = 0
                while j < len(checked_default_variables):
                    if checked_default_variables[j] in lines[i]:
                        print(
                            f"{path}: Line {i + 1}: S012 "
                            f"{Checker.MESSAGE_CODES['S012'].format(checked_default_variables[j])}")
                        checked_default_variables.remove(checked_default_variables[j])
                    else:
                        j += 1
