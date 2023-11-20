from odoo import api, fields, models, _
from odoo.http import request
import requests
import json
import base64
import hashlib
import os
import hmac
import uuid
from Crypto.Cipher import AES
from datetime import datetime
import pytz
from odoo.exceptions import UserError

class MubapayPayment(models.Model):
    _name = "mubapay.payment"
    _description = "Mubapay Payment"

    merchant_username = fields.Char(string='Token')
    merchant_password = fields.Float(string='PIN')
    device_id = fields.Char(string='Device ID', readonly=True)

    # def get_mac_address(self):
        # mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(5, -1, -1)])
        # return mac
    
    def generate_unique_device_code(self):
        obj = self.env['mubapay.payment']
        # mac_address = obj.get_mac_address()
        # # print(mac_address)
        ip_address = request.httprequest.environ['REMOTE_ADDR']
        mac_address = get_mac_address(ip=ip_address)
        unique_code = hashlib.md5(mac_address.encode()).hexdigest()[:16]
        final = str(unique_code)
        return final
    
    def check_device_id(self, user):
        obj = self.env['mubapay.payment']
        usr_obj = self.env['allowed.device'].browse(user)
        device_id = usr_obj.device_id
        matching = obj.generate_unique_device_code()
        
        if device_id == matching:
            return True
        else:
            raise UserError("""
                Device Ini tidak diijinkan untuk transaksi.
                Device ID: [ %s ]
            """ % matching)

    def get_formatted_datetime(self):
        utc_now = datetime.utcnow()
        utc_timezone = pytz.timezone('UTC')
        jakarta_timezone = pytz.timezone('Asia/Jakarta')
        current_datetime = utc_timezone.localize(utc_now).astimezone(jakarta_timezone)
        date_format = "%Y%m%d%H%M%S"
        formatted_datetime = current_datetime.strftime(date_format)
        
        return formatted_datetime
    
    def get_formatted_timestamp(self):
        utc_now = datetime.utcnow()
        utc_timezone = pytz.timezone('UTC')
        jakarta_timezone = pytz.timezone('Asia/Jakarta')
        wib_now = utc_timezone.localize(utc_now).astimezone(jakarta_timezone)
        date_format = "%d-%m-%Y %H:%M:%S"
        formatted_datetime = wib_now.strftime(date_format)
        
        return formatted_datetime

    def pad(self, byte_array):
        BLOCK_SIZE = 16
        pad_len = BLOCK_SIZE - len(byte_array) % BLOCK_SIZE
        return byte_array + (bytes([pad_len]) * pad_len)
    
    def encrypt(self, secret_key, header):
        obj = self.env['mubapay.payment']
        byte_array = secret_key.encode("UTF-8")
        padded = obj.pad(byte_array)
        iv = os.urandom(AES.block_size)
        cipher = AES.new( header.encode("UTF-8"), AES.MODE_CBC, iv )
        encrypted = cipher.encrypt(padded)
    
        return base64.b64encode(iv+encrypted).decode("UTF-8")
    
    def create_signature(self, payload, secret_key):
        hash_algorithm = hashlib.sha256
        key = secret_key.encode('utf-8')
        hmac_obj = hmac.new(key, msg=payload.encode('utf-8'), digestmod=hash_algorithm)
        hmac_bytes = hmac_obj.digest()
        signature = base64.b64encode(hmac_bytes).decode()
    
        return signature
    
    def create_payload(self, path, verb, token, timestamp, body):
        payload = f"path={path}&verb={verb}&token={token}&timestamp={timestamp}&body={body}"
        return payload


    def get_response(self, url, secret_key, header, datetime_str):
        obj = self.env['mubapay.payment']
        body = '{"datetime": "' + datetime_str + '"}'
        authorization = obj.encrypt(header, secret_key)
        payload = obj.create_payload("api/signin", "POST", authorization, datetime_str, body)
        signature = obj.create_signature(payload, secret_key)
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': authorization,
            'Signature': signature
        }
        
        data = {
            'datetime': datetime_str
        }
        
        response = requests.post(url, headers=headers, data=json.dumps(data))
        
        return response
    
    def create_payload_trx(self, path, verb, username, timestamp, santriqr):
        payload = f"path={path}&verb={verb}&username={username}&timestamp={timestamp}&santriqr={santriqr}"
        return payload
    
    def get_token(self, user):
        obj = self.env['mubapay.payment']
        usr_obj = self.env['allowed.device'].browse(user)
        merchant =  usr_obj.merchant_user
        passwd = usr_obj.passwd
        device_id = usr_obj.device_id
        obj.check_device_id(user)
        url = 'https://devops.usid.co.id:1123/siponpes/api/signin'
        secret_key = '4pMmH6LcWdclcMdRI5fCyXs19GanYsh3'
        datetime_str = obj.get_formatted_datetime()
            # user = self.username
            # password = self.password
        header = f"{merchant}-{passwd}-{device_id}" 
        resp = obj.get_response(url, secret_key, header, datetime_str)
        response =  resp.status_code
        if response == 200:
            response_data = resp.json()
            token = response_data.get("token")
            #update field token_val 
        else:
            raise UserError("""
                Ups Generate Token Gagal !
                Pastikan Device ID sudah Terdaftar
            """)
        return token
    
    @api.model
    def do_trx(self, totalPrice, santriQR, pin_pass, user):
        obj = self.env['mubapay.payment']
        usr_obj = self.env['allowed.device'].browse(user)
        timestamp = obj.get_formatted_timestamp()
        username =  usr_obj.merchant_user
        secret_key = '4pMmH6LcWdclcMdRI5fCyXs19GanYsh3'
        url_trx = f'https://devops.usid.co.id:1123/siponpes/toko/transaksi?username={username}'
        timestamp = timestamp
        seq = self.env['ir.sequence'].next_by_code('pos.order')
        
        body = {
            "nota": seq,
            "keterangan": "oke",
            "total": totalPrice,
            "qty": 1
        }
        
        payload = obj.create_payload_trx("toko/transaksi", "POST", username, timestamp, santriQR)
        signature = obj.create_signature(payload, secret_key)
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': obj.get_token(user),
            'Signature': signature,
            'SantriQR': santriQR,
            'Timestamp': timestamp,
            'SandiPIN' : pin_pass
        }
        
        # print("payload : " + payload)
        responses = requests.post(url_trx, headers=headers, data=json.dumps(body))
        resp_data = responses.json()
        status =  responses.status_code
        if status == 200:
            resp_data = responses.json()
            # token = response_data.get("status")
        else:
            print("Gagal! Kode Status:", responses.status_code)
           
        print(resp_data)
        return resp_data

        
