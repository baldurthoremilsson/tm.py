#!/usr/bin/env python

import sys
import re

state_regex = re.compile('^([a-zA-Z0-9]+)(!)?\n')
rule_regex = re.compile('^  ([a-zA-Z0-9]+) ([a-zA-Z0-9]+) ([<>])([a-zA-Z0-9]+)\n$')
# FIXME: only possible input is a-zA-Z0-9 = almost anything should be allowed

class Link(object):
    def __init__(self):
        self.val = None
        self.left = None
        self.right = None

    def grow_left(self):
        if self.left != None:
            raise Exception('Can not grow, left link already exists')
        self.left = Link()
        self.left.right = self

    def grow_right(self):
        if self.right != None:
            raise Exception('Can not grow, right link already exists')
        self.right = Link()
        self.right.left = self


class Tape(object):
    def __init__(self, contents):
        self.cursor = self.beginning = self.end = Link()
        for s in contents:
            self.write(s)
            self.right()
        self.cursor = self.beginning

    @property
    def contents(self):
        values = []
        iterator = self.beginning
        while iterator:
            if iterator.val:
                values.append(iterator.val)
            iterator = iterator.right
        return ''.join(values)

    def write(self, letter):
        self.cursor.val = letter

    def read(self):
        return self.cursor.val

    def left(self):
        if self.cursor == self.beginning:
            self.cursor.grow_left()
            self.cursor = self.beginning = self.cursor.left
        else:
            self.cursor = self.cursor.left

    def right(self):
        if self.cursor == self.end:
            self.cursor.grow_right()
            self.cursor = self.end = self.cursor.right
        else:
            self.cursor = self.cursor.right


class State(object):
    def __init__(self, name, final=False):
        self.name = name
        self.final = final
        self._actions = {}

    def __repr__(self):
        return u'<State {}>'.format(self.name)

    def run(self, tape):
        action = self._actions.get(tape.read())
        if action:
            return action(tape)

    def add_action(self, input, output, direction, next):
        self._actions[input] = self._action(output, direction, next)

    def _action(self, output, direction, next):
        def inner(tape):
            tape.write(output)
            if direction == '<':
                tape.left()
            elif direction == '>':
                tape.right()
            else:
                raise Exception('Unkown direction: {}'.format(direction))
            return next
        return inner


def parse(program):
    states = {}
    current_state = None
    firststate = None
    for line in program:
        if not line.strip():
            continue

        m = state_regex.match(line)
        if m:
            name = m.groups()[0]
            final = m.groups()[1] == '!'
            current_state = (State(name, final), [])
            states[name] = current_state
            if not firststate:
                firststate = current_state[0]
            continue

        m = rule_regex.match(line)
        if m:
            current_state[1].append(m.groups())
            continue
        print('error')

    for name, (state, rules) in states.iteritems():
        for rule in rules:
            _input = rule[0]
            _output = rule[1]
            _direction = rule[2]
            try:
                _next = states[rule[3]][0]
            except KeyError:
                raise Exception('No rule named {}'.format(rule[3]))

            state.add_action(_input, _output, _direction, _next)

    return firststate


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Use: {} filename'.format(sys.argv[0]))
        sys.exit(1)
    filename = sys.argv[1]
    with open(filename, 'r') as f:
        program = f.readlines()

    tape = Tape(sys.stdin.read())
    prog = parse(program)
    while prog:
        final = prog.final
        prog = prog.run(tape)

    print(tape.contents)
    if not final:
        sys.exit(1)
