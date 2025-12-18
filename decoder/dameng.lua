dameng_protocol = Proto("Dameng", "Dameng Protocol")
 
local head_packet_type_desc = {
    [0x01]  = "Login",
    [0x05]  = "SQL Request",
    [0xa3]  = "Login ACK",
	[0xbb]  = "Response",
    [0xc8]  = "Version",
	[0xe4]  = "Version",
}
 
local DAMENG_ie = {
	head_packet_type = ProtoField.uint16("dameng.head_packet_type", "HeadPacketType", base.HEX, head_packet_type_desc),
	data_len = ProtoField.uint16("dameng.date_len", "DataLen", base.DEC),
}
 
local login_ie = {
	username_len = ProtoField.uint32("dameng.username_len", "UserNameLen", base.DEC),
	username = ProtoField.bytes("dameng.username", "UserName"),
	password_len = ProtoField.uint32("dameng.password_len", "PassWordLen", base.DEC),
	password = ProtoField.bytes("dameng.password", "PassWord"),
	client_name_len = ProtoField.uint32("dameng.client_name_len", "ClientNameLen", base.DEC),
	client_name = ProtoField.string("dameng.client_name", "ClientName"),
	system_name_len = ProtoField.uint32("dameng.system_name_len", "SystemNameLen", base.DEC),
	system_name = ProtoField.string("dameng.system_name", "SystemName"),
	host_name_len = ProtoField.uint32("dameng.host_name_len", "HostNameLen", base.DEC),
	host_name = ProtoField.string("dameng.host_name", "HostName"),
}
 
local loginACK_ie = {
	db_name = ProtoField.string("dameng.db_name", "DataBaseName"),
	username = ProtoField.string("dameng.username", "UserName"),
	client_ip = ProtoField.string("dameng.client_ip", "ClientIP"),
	link_time = ProtoField.string("dameng.link_time", "LinkTime"),
}
 
local SQL_ie = {
	sql_data = ProtoField.string("dameng.sql_data", "SQL data"),
}
 
local Version_ie = {
	clinet_version = ProtoField.string("dameng.client_version", "Client Version"),
	server_version = ProtoField.string("dameng.server_version", "Server Version"),
}
 
dameng_protocol.fields = { 
	---------------DAMENG_ie----------------
	DAMENG_ie.head_packet_type,
	DAMENG_ie.data_len,
	---------------login_ie----------------
	login_ie.username_len,
	login_ie.username,
	login_ie.password_len,
	login_ie.password,
	login_ie.client_name_len,
	login_ie.client_name,
	login_ie.system_name_len,
	login_ie.system_name,
	login_ie.host_name_len,
	login_ie.host_name,
	---------------loginACK_ie----------------
	loginACK_ie.db_name,
	loginACK_ie.username,
	loginACK_ie.client_ip,
	loginACK_ie.link_time,
	---------------SQL_ie----------------
	SQL_ie.sql_data,
	---------------Version_ie----------------
	Version_ie.clinet_version,
	Version_ie.server_version,
}
 
function dameng_protocol.dissector(tvb, pinfo, tree)
    length = tvb:len()
    if length == 0 then
        return
    end
    pinfo.cols.protocol = dameng_protocol.name
	local offset = 0
	local msg_len = 0
	
    local subtree = tree:add(dameng_protocol, tvb(), "Dameng Protocol Data")
	offset = offset + 4
	local headPacketType = tvb(offset,2):le_uint()
	subtree:add_le(DAMENG_ie.head_packet_type, tvb(offset,2))
	offset = offset + 2
	local dataLen = tvb(offset,2):le_uint()
--	subtree:add_le(DAMENG_ie.data_len, tvb(offset,2))
	offset = offset + 2
	if (headPacketType == 0x01) then
	----------------dissect login-------------------
		offset = offset + 56
		----------------dissect username-------------------
		local usernameLen = tvb(offset,4):le_uint()
--		subtree:add_le(login_ie.username_len, tvb(offset,4))		
		offset = offset + 4
		subtree:add(login_ie.username, tvb(offset, usernameLen))
		offset = offset + usernameLen
		----------------dissect password-------------------
		local passwordLen = tvb(offset,4):le_uint()
--		subtree:add_le(login_ie.password_len, tvb(offset,4))
		offset = offset + 4		
		subtree:add(login_ie.password, tvb(offset, passwordLen))
		offset = offset + passwordLen
		----------------dissect client_name-------------------
		local clientNameLen = tvb(offset,4):le_uint()
--		subtree:add_le(login_ie.client_name_len, tvb(offset,4))
		offset = offset + 4		
		subtree:add(login_ie.client_name, tvb(offset, clientNameLen))
		offset = offset + clientNameLen
		----------------dissect system_name-------------------
		local systemNameLen = tvb(offset,4):le_uint()
--		subtree:add_le(login_ie.system_name_len, tvb(offset,4))
		offset = offset + 4		
		subtree:add(login_ie.system_name, tvb(offset, systemNameLen))
		offset = offset + systemNameLen
		----------------dissect host_name-------------------
		local hostNameLen = tvb(offset,4):le_uint()
--		subtree:add_le(login_ie.host_name_len, tvb(offset,4))
		offset = offset + 4		
		subtree:add(login_ie.host_name, tvb(offset, hostNameLen))
		offset = offset + hostNameLen
		
	elseif (headPacketType == 0xa3) then
	----------------dissect login ACK-------------------
		offset = offset + 72
		----------------dissect database name-------------------
		local dbNameLen = tvb(offset,4):le_uint()		
		offset = offset + 4
		subtree:add(loginACK_ie.db_name, tvb(offset, dbNameLen))
		offset = offset + dbNameLen
		----------------dissect user-------------------
		local userNameLen = tvb(offset,4):le_uint()
		offset = offset + 4		
		subtree:add(loginACK_ie.username, tvb(offset, userNameLen))
		offset = offset + userNameLen
		----------------dissect client_ip-------------------
		local clientIpLen = tvb(offset,4):le_uint()
		offset = offset + 4		
		subtree:add(loginACK_ie.client_ip, tvb(offset, clientIpLen))
		offset = offset + clientIpLen
		----------------dissect link time-------------------
		local linkTimeLen = tvb(offset,4):le_uint()
		offset = offset + 4		
		subtree:add(loginACK_ie.link_time, tvb(offset, linkTimeLen))
		offset = offset + linkTimeLen	
		
	elseif (headPacketType == 0x05) then
	----------------dissect SQL Request-------------------
		offset = offset + 56
		subtree:add(SQL_ie.sql_data, tvb(offset, dataLen))
	elseif (headPacketType == 0xc8) then
	----------------dissect Client Version-------------------
		offset = offset + 56
		local clientVersionLen = tvb(offset,4):le_uint()
--		subtree:add_le(login_ie.client_name_len, tvb(offset,4))
		offset = offset + 4		
		subtree:add(Version_ie.clinet_version, tvb(offset, clientVersionLen))
		offset = offset + clientVersionLen
	elseif (headPacketType == 0xe4) then
	----------------dissect Server Version-------------------
		offset = offset + 72
		local serverVersionLen = tvb(offset,4):le_uint()
--		subtree:add_le(login_ie.client_name_len, tvb(offset,4))
		offset = offset + 4		
		subtree:add(Version_ie.server_version, tvb(offset, serverVersionLen))
		offset = offset + serverVersionLen
	end
end
 
local tcp_port = DissectorTable.get("tcp.port")
tcp_port:add(5236, dameng_protocol)
