from odoo import api, fields, models, _
import requests
import json
import base64
import hashlib
import os
import hmac
from Crypto.Cipher import AES
from datetime import datetime
import pytz
from random import randint

def random_with_N_digits(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1
        
    return randint(range_start, range_end)

class MubapayPayment(models.Model):
    _name = "mubapay.payment"
    _description = "Mubapay Payment"

    merchant_username = fields.Char(string='Token')
    merchant_password = fields.Float(string='PIN')
    device_id = fields.Char(string='Device ID', readonly=True)

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
    
    def get_token(self):
        obj = self.env['mubapay.payment']
        url = 'https://devops.usid.co.id:1123/siponpes/api/signin'
        secret_key = '4pMmH6LcWdclcMdRI5fCyXs19GanYsh3'
        datetime_str = obj.get_formatted_datetime()
            # user = self.username
            # password = self.password
        header = "M000-123456-f796d4131c4a92e4"
        resp = obj.get_response(url, secret_key, header, datetime_str)
        response =  resp.status_code
        if response == 200:
            response_data = resp.json()
            token = response_data.get("token")
            #update field token_val 
        else:
            print("Gagal! Kode Status:", response.status_code)
        return token
    
    @api.model
    def do_trx(self, totalPrice, santriQR, pin_pass):
        obj = self.env['mubapay.payment']
        timestamp = obj.get_formatted_timestamp()
        username = 'M000'
        secret_key = '4pMmH6LcWdclcMdRI5fCyXs19GanYsh3'
        url_trx = f'https://devops.usid.co.id:1123/siponpes/toko/transaksi?username={username}'
        timestamp = timestamp
        santriqr = 'djAxnVg6ra8oRS+u2B1BuoP/6lQM+ywPSINcUVRSnt6Y2XrKNI/BDPawz8axiQ=='
        
        body = {
            "nota": "POS-" + str(random_with_N_digits(8)),
            "keterangan": "oke",
            "total": totalPrice,
            "qty": 1
        }
        
        payload = obj.create_payload_trx("toko/transaksi", "POST", username, timestamp, santriqr)
        signature = obj.create_signature(payload, secret_key)
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': obj.get_token(),
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

        
