-- by Filip Leszek, Dominik Łopatecki

-- copy to /wireshark/plugins/strumyk_dissector.lua
local strumyk_protocol = Proto("STRumyk", "STRumyk Protocol")

packet_type = ProtoField.int16("strumyk.packet_type", "PacketType", base.DEC)
session_id = ProtoField.int32("strumyk.session_id", "SessionId", base.DEC)
packet_number = ProtoField.int32("strumyk.packet_number", "PacketNumber", base.DEC)
control_type = ProtoField.int32("strumyk.control_type", "ControlType", base.DEC)
stream_id = ProtoField.int32("strumyk.stream_id", "StreamId", base.DEC)
timestamp = ProtoField.int32("strumyk.timestamp", "Timestamp", base.DEC)
data = ProtoField.string("strumyk.data", "Data", base.NONE)
requested_packet_number = ProtoField.int32("strumyk.requested_packet_number", "RequestedPacketNumber", base.DEC)

strumyk_protocol.fields = { packet_type, session_id, packet_number, control_type, stream_id, timestamp, data,
  requested_packet_number }

function strumyk_protocol.dissector(buffer, pinfo, tree)
  local length = buffer:len()
  if length == 0 then return end

  pinfo.cols.protocol = strumyk_protocol.name

  local subtree = tree:add(strumyk_protocol, buffer(), "STRumyk Protocol Data")

  -- getting packet type value
  local packet_type_val = buffer(0, 2):le_uint()

  -- fields in every packet types but ErrorPacket
  subtree:add_le(packet_type, buffer(0, 4))
  if packet_type_val ~= 6 then
    subtree:add_le(session_id, buffer(4, 4))
    subtree:add_le(packet_number, buffer(8, 4))
  end

  -- SessionControlPacket
  if packet_type_val == 1 then
    subtree:add_le(control_type, buffer(12, 4))
  end
  -- StreamControlPacket
  if packet_type_val == 2 then
    subtree:add_le(control_type, buffer(12, 4))
    subtree:add_le(stream_id, buffer(16, 4))
  end
  -- RetransmissionRequestPacket
  if packet_type_val == 3 then
    subtree:add_le(stream_id, buffer(12, 4))
    subtree:add_le(requested_packet_number, buffer(14, 4))
  end
  -- ConfirmationPacket
  if packet_type_val == 4 then
    subtree:add_le(stream_id, buffer(12, 4))
  end
  -- DataPacket
  if packet_type_val == 5 then
    subtree:add_le(stream_id, buffer(12, 4))
    subtree:add_le(timestamp, buffer(16, 4))

    local data_length = length - 18
    subtree:add_le(data, buffer(19, data_length - 1))
  end
end

local udp_port = DissectorTable.get("udp.port")
udp_port:add(8004, strumyk_protocol)
udp_port:add(8005, strumyk_protocol)
