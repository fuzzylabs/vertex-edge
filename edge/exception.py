class EdgeException(Exception):
    def __init__(self, mesg: str, fatal: bool = True):
        self.fatal = True
        super(EdgeException, self).__init__(mesg)
