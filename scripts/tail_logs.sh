#!/bin/bash
# Direct real-time log tail - shows everything
sshpass -p "0212Connect!" ssh -o StrictHostKeyChecking=no root@47.117.176.214 "tail -f /moqiyouxi_backend/server.log"

