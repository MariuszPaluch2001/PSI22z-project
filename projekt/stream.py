class Stream:
    def __init__(self,stream_id, my_address, my_port,host_address,host_port,logger) -> None:
        self.stream_id = stream_id
        self.my_address = my_address
        self.my_port = my_port
        self.host_address = host_address
        self.host_port = host_port
        self.logger = logger
        self.message_buffer = []

    def close():
        pass

    def is_closed():
        pass


class ClientStream(Stream):
    def __init__(self, stream_id, my_address, my_port, host_address, host_port, logger) -> None:
        super().__init__(stream_id, my_address, my_port, host_address, host_port, logger)


    def get_message(self):
        pass

    def get_all_messages(self):
        pass


class ServerStream(Stream):
    def __init__(self, stream_id, my_address, my_port, host_address, host_port, logger) -> None:
        super().__init__(stream_id, my_address, my_port, host_address, host_port, logger)

    def put_message(self, message)
        pass