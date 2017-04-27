from utilities import OrderedSet
import re, copy, itertools

class Grammar:
    """Class that represents a grammar. It works with the prefix notation."""
    
    NT = "NT"
    T = "T"
    
    def __init__(self, grammar_path = None, max_rec_level = 3):
        if grammar_path == None:
            raise Exception("Grammar file not detected!!")
        else:
            self.grammar_file = grammar_path
        self.grammar = {}
        self.productions_labels = {}
        self.non_terminals, self.terminals = set(), set()
        self.ordered_non_terminals = OrderedSet()
        self.start_rule = None
        self.max_recursion_level = max_rec_level
        self.number_of_references_by_non_terminal = {}
        self.read_grammar()
        self.compute_count_references_to_non_terminals()


    def derivation_tree(self, mapping_rules):
        return self.new_build_tree(self.start_rule, [0], [0], mapping_rules, [0] * len(mapping_rules), 0)


    def new_build_tree(self, current_sym, wraps, count, mapping_rules, mapping_values, len_choices):
        if current_sym[1] == self.T:
            return current_sym
        current_sym_pos = self.ordered_non_terminals.index(current_sym[0])
        choices = self.grammar[current_sym[0]]
        current_production = mapping_rules[current_sym_pos][0][mapping_values[current_sym_pos]]
        mapping_values[current_sym_pos] += 1
        final = []
        for i in choices[current_production]:
            temp = self.new_build_tree(i, wraps, count, mapping_rules, mapping_values, len(choices))
            if temp == None:
                return None
            final.append(temp)

        return (current_sym[0], final)


    def read_grammar(self):
        """
        Reads a grammar in the BNF format and converts it to a python dictionary. If the grammar is recursive, it transforms the recursive productions in non-recursive ones.
        This method was adapted from PonyGE version 0.1.3 by Erik Hemberg and James McDermott.
        """

        nt_pattern = "(<.+?>)"
        rule_separator = "::="
        production_separator = "|"
        f = open(self.grammar_file, "r")
        for line in f:
            if not line.startswith("#") and line.strip() != "":
                if line.find(rule_separator):
                    left_side, productions = line.split(rule_separator)
                    left_side = left_side.strip()
                    if not re.search(nt_pattern, left_side):
                        raise ValueError("left side not a non-terminal!")
                    self.non_terminals.add(left_side)
                    self.ordered_non_terminals.add(left_side)
                    if self.start_rule == None:
                        self.start_rule = (left_side, self.NT)
                    temp_productions = []
                    for production in [production.strip() for production in productions.split(production_separator)]:
                        temp_production = []
                        if not re.search(nt_pattern, production):
                            if production == "None":
                                production = ""
                            self.terminals.add(production)
                            temp_production.append((production, self.T))
                        else:
                            for value in re.findall("<.+?>|[^<>]*", production):
                                if value != "":
                                    if re.search(nt_pattern, value) == None:
                                        sym = (value, self.T)
                                        self.terminals.add(value)
                                    else:
                                        sym = (value, self.NT)
                                    temp_production.append(sym)
                        temp_productions.append(temp_production)
                    if left_side not in self.grammar:
                        self.grammar[left_side] = temp_productions
        f.close()
        recursive, nt = self.is_recursive()
        while recursive:
            self.rewrite_production(nt)
            recursive, nt = self.is_recursive()


    def is_recursive(self):
        """
        Verifies if a grammar is recursive, and return the first non-terminal where there is recursion
        """

        for key in self.ordered_non_terminals:
            for options in self.grammar[key]:
                for option in options:
                    if option[1] == self.NT and option[0] == key:
                        return (True, key)
        return (False, None)


    def rewrite_production(self, nt):
        MAX_REC_LEVEL = self.max_recursion_level
        new_non_terminals = []
        new_grammar = copy.deepcopy(self.grammar)
        new_terminal_stub = nt[0 : -1] + "_lvl_%d>"
        initial_options = copy.deepcopy(self.grammar[nt])
        last_level = None
        for lvl in xrange(0, MAX_REC_LEVEL+1):
            if lvl == 0:
                grammar_options = new_grammar[nt]
            else:
                grammar_options = copy.deepcopy(initial_options)
            for options in grammar_options:
                for index, option in enumerate(options):
                    if option[1] == self.NT and option[0] == nt:
                        current_level = new_terminal_stub % lvl
                        t_option = (current_level, option[1])
                        options[index] = t_option
                if lvl !=0:
                    new_grammar[last_level] = grammar_options
            new_non_terminals += [current_level]
            last_level = current_level

        last_production = []
        non_recursive_productions = self.list_non_recursive_productions(nt)
        for production in initial_options:
            nr_productions = self.create_non_recursive_productions(production, non_recursive_productions, nt)
            last_production.extend(nr_productions)

        new_grammar[last_level] = last_production
        self.grammar = new_grammar
        self.non_terminals.update(new_non_terminals)
        for e in new_non_terminals:
            self.ordered_non_terminals.add(e)


    def create_non_recursive_productions(self, production, non_recursive_productions, nt):
        productions = []
        for index, symbol in enumerate(production):
            if symbol[0] == nt:
                for nr_production in non_recursive_productions:
                    temp_production = copy.deepcopy(production)
                    del temp_production[index]
                    temp_production[index:index] = nr_production
                    new_productions = self.create_non_recursive_productions(temp_production, non_recursive_productions, nt)
                    productions.extend(new_productions)
                break
        else:
            productions.append(production)

        return productions


    def get_non_terminals(self):
        return self.ordered_non_terminals


    def list_non_recursive_productions(self, nt):
        non_recursive_elements = []
        for options in self.grammar[nt]:
            for option in options:
                if option[1] == self.NT and option[0] == nt:
                    break
            else:
                non_recursive_elements += [options]
        return non_recursive_elements


    def mapping(self, mapping_rules, positions_to_map):
        wraps = 0
        count = 0
        output = []
        choices = []
        rules_to_expand = [self.start_rule]
        while len(rules_to_expand) > 0:
            current_sym = rules_to_expand.pop(0)
            if current_sym[1] == self.T:
                output.append(current_sym[0])
            else:
                current_sym_pos = self.ordered_non_terminals.index(current_sym[0])
                choices = self.grammar[current_sym[0]]
                current_production = mapping_rules[current_sym_pos][0][positions_to_map[current_sym_pos]]
                positions_to_map[current_sym_pos] += 1
                next_to_expand = choices[current_production]
                rules_to_expand = next_to_expand + rules_to_expand
        output = "".join(output)
        output = self.python_filter(output)
        return output


    def count_number_of_non_terminals(self):
        return len(self.ordered_non_terminals)


    def count_number_of_options_in_production(self):
        number_of_options_by_non_terminal = {}
        g = self.grammar
        for nt in self.ordered_non_terminals:
            number_of_options_by_non_terminal.setdefault(nt, len(g[nt]))
        return number_of_options_by_non_terminal


    def get_total_references(self, di, nt):
        soma = 0
        if nt == '<start>':
            return 1
        for k in di[nt].keys():
            soma += di[nt][k]
        return soma


    def compute_list_size(self, nt, is_referenced_by, count_references_by_prod, value):
        references = self.get_total_references(count_references_by_prod, nt)
        result = []
        if nt == '<start>':
            return 1
        for ref in is_referenced_by[nt]:
            result.append(self.compute_list_size(ref, is_referenced_by, count_references_by_prod, references))
        references *= max(result)
        return references


    def recursive_version(self, is_referenced_by, count_references_by_prod):
        count_stuff = {}
        count_references_in_prod = {}
        for i in self.non_terminals:
            count_stuff[i] = self.compute_list_size(i, is_referenced_by, count_references_by_prod, 1)
        return count_stuff


    def compute_count_references_to_non_terminals(self):
        import re
        def natural_key(string_):
            return [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', string_)]
        g = self.grammar
        count_references_in_prod = {}
        is_referenced_by = {}
        references = {}
        temp_ordered = OrderedSet(sorted(list(self.ordered_non_terminals), key=natural_key))
        for nt in temp_ordered:
            for production in g[nt]:
                count_temp = {}
                for option in production:
                    if option[1] == self.NT:
                        is_referenced_by.setdefault(option[0], set())
                        is_referenced_by[option[0]].add(nt)
                        references.setdefault(nt, set())
                        references[nt].add(option[0])
                        count_temp.setdefault(option[0],0)
                        count_temp[option[0]] += 1
                for key in count_temp:
                    count_references_in_prod.setdefault(key, {})
                    count_references_in_prod[key].setdefault(nt, 0)
                    count_references_in_prod[key][nt] = max(count_references_in_prod[key][nt], count_temp[key])
        self.number_of_references_by_non_terminal = self.recursive_version(is_referenced_by, count_references_in_prod)
        return self.number_of_references_by_non_terminal


    def count_references_to_non_terminals(self):
        return  self.number_of_references_by_non_terminal

    def python_filter(self, txt):
        """ Create correct python syntax.
        We use {: and :} as special open and close brackets, because
        it's not possible to specify indentation correctly in a BNF
        grammar without this type of scheme.
        This method was adapted from PonyGE version 0.1.3 by Erik Hemberg and James McDermott.
        """

        txt = txt.replace("\le", "<=")
        txt = txt.replace("\ge", ">=")
        txt = txt.replace("\l", "<")
        txt = txt.replace("\g", ">")
        txt = txt.replace("\eb", "|")
        indent_level = 0
        tmp = txt[:]
        i = 0
        while i < len(tmp):
            tok = tmp[i:i+2]
            if tok == "{:":
                indent_level += 1
            elif tok == ":}":
                indent_level -= 1
            tabstr = "\n" + "  " * indent_level
            if tok == "{:" or tok == ":}" or tok == "\\n":
                tmp = tmp.replace(tok, tabstr, 1)
            i += 1
            txt = "\n".join([line for line in tmp.split("\n") if line.strip() != ""])
        return txt


    def __str__(self):
        grammar = self.grammar
        #print self.grammar
        print self.count_references_to_non_terminals()
        text = ""
        for key in self.ordered_non_terminals:
            text += key + " ::= "
            for options in grammar[key]:
                for option in options:
                    text += option[0]
                if options != grammar[key][-1]:
                    text += " | "
            text += "\n"
        return text
