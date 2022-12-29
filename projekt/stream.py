class Stream:
    def __init__(self,stream_id,logger) -> None:
        self.stream_id = stream_id

        self.logger = logger
        self.message_buffer_in = []
        self.message_buffer_out = []

    def close():
        ...

    def is_closed():
        ...

    def get_message(self):
        ...

    def get_all_messages(self):
        ...

    def put_message(self, binary_stream):
        ...
    
    def process_control_packets(self):
        raise NotImplementedError()

class ClientStream(Stream):
    def __init__(self, stream_id, logger) -> None:
        super().__init__(stream_id, logger)

    def process_control_packets(self):
        ...

class ServerStream(Stream):
    def __init__(self, stream_id, logger) -> None:
        super().__init__(stream_id, logger)

    def process_control_packets(self):
        ...