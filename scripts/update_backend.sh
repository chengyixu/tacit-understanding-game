#!/bin/bash

# Script to update the backend word_bank.json on server
# Server details:
# Host: 43.137.34.201
# Username: root
# Password: 0212Connect!

echo "Updating word_bank.json on backend server..."
echo "Please make sure you have SSH access to the server."
echo ""
echo "To manually update the file, use these commands:"
echo "1. First, copy the file to server:"
echo "   scp word_bank.json root@43.137.34.201:/tmp/"
echo ""
echo "2. Then SSH into server and move it:"
echo "   ssh root@43.137.34.201"
echo "   mv /tmp/word_bank.json /moqiyouxi_backend/"
echo ""
echo "Or use password with sshpass:"
echo "   sshpass -p '0212Connect!' scp word_bank.json root@43.137.34.201:/moqiyouxi_backend/"
echo ""
echo "Note: The enriched word_bank.json now contains:"
echo "- 20 words per category (increased from 10)"
echo "- 20 total categories (increased from 12)"
echo "- New categories: 美食, 汽车品牌, 电影, 运动项目, 学科, 节日, 颜色, 动物"