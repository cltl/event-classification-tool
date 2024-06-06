class QuoteConverter:
    def __init__(self):
        self.open_quote = False

    def replace_with_curly_quotes(self, text):
        result = []
        for char in text:
            if char == '"' and not self.open_quote:
                result.append('“')
                self.open_quote = True
            elif char == '"' and self.open_quote:
                result.append('”')
                self.open_quote = False
            else:
                result.append(char)
        return ''.join(result)