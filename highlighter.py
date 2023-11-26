from PySide6 import QtCore, QtGui

def format(color, style=''):
    """Return a QTextCharFormat with the given attributes.
    """
    _color = QtGui.QColor()
    _color.setNamedColor(color)

    _format = QtGui.QTextCharFormat()
    _format.setForeground(_color)
    if 'bold' in style:
        _format.setFontWeight(QtGui.QFont.Bold)
    if 'italic' in style:
        _format.setFontItalic(True)

    return _format


# Syntax styles that can be shared by all languages
STYLES = {
    'keyword': format('blue'),
    'operator': format('red'),
    'brace': format('green', 'bold'),
    'types': format('orange', 'bold'),
    'string': format('magenta'),
    'string2': format('darkMagenta'),
    'comment': format('darkGreen', 'italic'),
    'numbers': format('brown'),
}


class VHDLHighlighter (QtGui.QSyntaxHighlighter):
    """Syntax highlighter for the language.
    """
    # Python keywords
    keywords = [
        'and', 'or', 'xor', 'xnor', 'not', 'nor', 'nand',
        'if','elsif', 'else', 'then'  
        'case', 'when'
        'for', 'while', 'use', 'wait', 'report', 
        'in', 'out', 'inout', 'bidir',
        'is',
        'architecture', 'entity', 'process', 'port', 'begin', 'end', 'of', 'signal', 'variable'
    ]

    # operators
    operators = [
        '<=', ':',
        # Comparison
        '=', '/=', '<', '<=', '>', '>=',
        # Arithmetic
        '\+', '-', '\*', '/', '//',  '\*\*',
    ]

    # braces
    braces = [
        '\{', '\}', '\(', '\)', '\[', '\]',
    ]

    types = [
        'std_logic', 'integer', 'string'
    ]

    def __init__(self, parent: QtGui.QTextDocument) -> None:
        super().__init__(parent)


        rules = []

        # Keyword, operator, and brace rules
        rules += [(r'(\b%s\b)' % w, 0, STYLES['keyword'])
            for w in VHDLHighlighter.keywords]
        rules += [(r'%s' % o, 0, STYLES['operator'])
            for o in VHDLHighlighter.operators]
        rules += [(r'%s' % b, 0, STYLES['brace'])
            for b in VHDLHighlighter.braces]
        rules += [(r'%s' % t, 0, STYLES['types'])
            for t in VHDLHighlighter.types]

        # All other rules
        rules += [

            # Numeric literals
            (r'\b[+-]?[0-9]+[lL]?\b', 0, STYLES['numbers']),
            (r'\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b', 0, STYLES['numbers']),
            (r'\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b', 0, STYLES['numbers']),

            # Double-quoted string, possibly containing escape sequences
            (r'"[^"\\]*(\\.[^"\\]*)*"', 0, STYLES['string']),
            # Single-quoted string, possibly containing escape sequences
            (r"'[^'\\]*(\\.[^'\\]*)*'", 0, STYLES['string']),

            # From '#' until a newline
            (r'--[^\n]*', 0, STYLES['comment']),
        ]

        # Build a QRegExp for each pattern
        self.rules = [(QtCore.QRegularExpression(pat), index, fmt)
            for (pat, index, fmt) in rules]

    def highlightBlock(self, text):
        """Apply syntax highlighting to the given block of text.
        """
        self.tripleQuoutesWithinStrings = []
        # Do other syntax formatting
        
        for expression, nth, format in self.rules:
            matches = []
            index = expression.globalMatch(text.lower())
            while index.hasNext():
                match = index.next()
                matches.append(match)
            for i in matches:
                if i.capturedStart() >= 0:
                    self.setFormat(i.capturedStart(), i.capturedLength(), format)

        self.setCurrentBlockState(0)