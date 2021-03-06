import random
import aes
from hashlib import sha256
import hmac

prime = 0xffffffffffffffffc90fdaa22168c234c4c6628b80dc1cd129024e088a67cc74020bbea63b139b22514a08798e3404ddef9519b3cd3a431b302b0a6df25f14374fe1356d6d51c245e485b576625e7ec6f44c42e9a637ed6b0bff5cb6f406b7edee386bfb5a899fa5ae9f24117c4b1fe649286651ece45b3dc2007cb8a163bf0598da48361c55d39a69163fa8fd24cf5f83655d23dca3ad961c62f356208552bb9ed529077096966d670c354e4abc9804f1746c08ca237327ffffffffffffffff
generator = 2

def keygen(p, g):
    a = random.randrange(1, p-1)
    A = pow(g, a, p)
    return a, A

def hex_os2i(os):
    return long('0x' + os, 16)

class player:
    def __init__(self, mail, pw):
        self.mail = mail
        self.pw = pw

    def compute_u(self):
        uH = sha256(str(self.A) + str(self.B)).hexdigest()
        self.u = hex_os2i(uH)

    def sign_salt(self):
        return hmac.new(self.K, self.salt, sha256).hexdigest()
    
class client(player):
    @staticmethod
    def setup(mail, pw):
        p = client(mail, pw)
        p.N = prime
        p.g = generator
        p.k = 3
        return p

    def get_login(self):
        self.a, self.A = keygen(self.N, self.g)
        return self.mail, self.A

    def recv_salt(self, salt, pubkey):
        self.salt = salt
        self.B = pubkey

    def compute_K(self):
        self.compute_u()

        xH = sha256(self.salt + self.pw).hexdigest()
        x = hex_os2i(xH)
        gx = pow(self.g, x, self.N)
        S = pow(self.B - self.k * gx, self.a + self.u * x, self.N)
        self.K = sha256(str(S)).digest()

    def compute_K0(self):
        self.K = sha256(str(long(0))).digest()
    
class server(player):
    @staticmethod
    def setup(mail, pw):
        p = server(mail, pw)
        p.N = prime
        p.g = generator
        p.k = 3
        p.salt = aes.generateRandomKey(16)
        xH = sha256(p.salt + pw).hexdigest()
        x = hex_os2i(xH)
        p.v = pow(p.g, x, p.N)
        return p

    def recv_login(self, mail, pubkey):
        assert self.mail == mail
        self.A = pubkey

    def get_salt(self):
        self.b, self.B = keygen(self.N, self.g)
        self.B = (self.B + self.k * self.v) % self.N
        return self.salt, self.B

    def compute_K(self):
        self.compute_u()

        vu = pow(self.v, self.u, self.N)
        S = pow(self.A * vu, self.b, self.N)
        self.K = sha256(str(S)).digest()

    def recv_mac(self, mac):
        assert self.sign_salt() == mac
        self.result = 'ok'

if __name__ == '__main__':
    mail = 'jpixton@gmail.com'
    pw = 'fartbutts'
    server = server.setup(mail, pw)
    client = client.setup(mail, pw)

    mail, pubkey = client.get_login()
    client.A = 0
    server.recv_login(client.mail, client.A)
    client.recv_salt(*server.get_salt())
    server.compute_K()
    client.compute_K0()
    server.recv_mac(client.sign_salt())
    assert server.result == 'ok'
    
    print('ok')
