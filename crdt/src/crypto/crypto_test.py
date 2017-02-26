from binascii import hexlify

from crypto.DiffieHellman import DiffieHellman

if __name__ == '__main__':
    a = DiffieHellman(keyLength=180)
    b = DiffieHellman(keyLength=180)
    a.genKey(b.publicKey)
    b.genKey(a.publicKey)

    if a.getKey() == b.getKey():
        print("Shared keys match.")
        print("Key:", hexlify(a.getKey()))
