import binascii
from unittest import TestCase

import base58

from bitmerchant.network import BitcoinTestNet
from bitmerchant.wallet.keys import ChecksumException
from bitmerchant.wallet.keys import IncompatibleNetworkException
from bitmerchant.wallet.keys import KeyParseError  # TODO test this
from bitmerchant.wallet.keys import PrivateKey
from bitmerchant.wallet.keys import PublicKey


class _TestPrivateKeyBase(TestCase):
    def setUp(self):
        # This private key chosen from the bitcoin docs:
        # https://en.bitcoin.it/wiki/Wallet_import_format
        self.expected_key = \
            "0c28fca386c7a227600b2fe50b7cae11ec86d3bf1fbe471be89827e19d72aa1d"
        self.key = PrivateKey(long(self.expected_key, 16))


class _TestPublicKeyBase(TestCase):
    def setUp(self):
        # This private key chosen from the bitcoin docs:
        # https://en.bitcoin.it/wiki/Wallet_import_format
        self.expected_private_key = \
            "18e14a7b6a307f426a94f8114701e7c8e774e7f9a47e2c2035db29a206321725"
        self.private_key = PrivateKey(long(self.expected_private_key, 16))
        self.public_key = PublicKey.from_hex_key(
            "04"
            "50863ad64a87ae8a2fe83c1af1a8403cb53f53e486d8511dad8a04887e5b2352"
            "2cd470243453a299fa9e77237716103abc11a1df38855ed6f2ee187e9c582ba6")


class TestPrivateKey(_TestPrivateKeyBase):
    def test_raw_key_hex(self):
        exp = self.key.private_exponent
        self.assertEqual(PrivateKey(exp), self.key)

    def test_raw_key_hex_bytes(self):
        key = binascii.unhexlify(self.key.get_key())
        self.assertEqual(PrivateKey.from_hex_key(key), self.key)

    def test_from_master_password(self):
        password = "correct horse battery staple"
        expected_wif = "5KJvsngHeMpm884wtkJNzQGaCErckhHJBGFsvd3VyK5qMZXj3hS"
        expected_pub_address = "1JwSSubhmg6iPtRjtyqhUYYH7bZg3Lfy1T"

        key = PrivateKey.from_master_password(password)
        self.assertEqual(key.export_to_wif(), expected_wif)
        self.assertEqual(
            key.get_public_key().to_address(), expected_pub_address)


class TestWIF(_TestPrivateKeyBase):
    def setUp(self):
        super(TestWIF, self).setUp()
        self.expected_wif = \
            '5HueCGU8rMjxEXxiPuD5BDku4MkFqeZyd4dZ1jvhTVqvbTLvyTJ'

    def test_export_to_wif(self):
        self.assertEqual(
            self.key.export_to_wif(),
            self.expected_wif)

    def test_import_wif(self):
        key = PrivateKey.from_wif(self.expected_wif)
        self.assertEqual(key, self.key)

    def test_import_wif_invalid_network(self):
        self.assertRaises(
            IncompatibleNetworkException, PrivateKey.from_wif,
            self.key.export_to_wif(), BitcoinTestNet)

    def test_import_wif_network(self):
        # Make a wif for bitcoin testnet:
        testnet_key = PrivateKey(
            self.key.private_exponent, network=BitcoinTestNet)
        testnet_wif = testnet_key.export_to_wif()
        # We should be able to load it properly
        key = PrivateKey.from_wif(testnet_wif, BitcoinTestNet)
        self.assertEqual(testnet_key, key)

    def test_bad_checksum(self):
        wif = self.key.export_to_wif()
        bad_checksum = base58.b58encode(binascii.unhexlify('FFFFFFFF'))
        wif = wif[:-8] + bad_checksum
        self.assertRaises(ChecksumException, PrivateKey.from_wif, wif)


class TestPublicKey(_TestPublicKeyBase):
    def test_leading_zeros(self):
        # This zero-leading x coordinate generated by:
        # pvk = '18E14A7B6A307F426A94F8114701E7C8E774E7F9A47E2C2035DB29A206321725'  # nopep8
        # pubkey = Public_key(SECP256k1.generator, SECP256k1.generator * long(pvk, 16))  # nopep8
        # for i in range(1, 10000):
        # x = (pubkey.point * i).x()
        # k = keys.long_to_hex(x, 64)
        # if k.startswith('0'):
        #     print i
        #     break
        expected_key = (
            "04"
            "02cbfd5410fd04973c096a4275bf75070955ebd689f316a6fbd449980ba7b756"
            "c559764e5c367c03e002751aaf4ef8ec40fe97cda9b2d3f14fdd4cd244e8fcd2")
        public_key = PublicKey.from_hex_key(expected_key)
        self.assertEqual(public_key.get_key(), expected_key)

    def test_address(self):
        expected_address = "16UwLL9Risc3QfPqBUvKofHmBQ7wMtjvM"
        actual_address = self.public_key.to_address()
        self.assertEqual(expected_address, actual_address)

    def test_private_to_public(self):
        self.assertEqual(
            self.private_key.get_public_key(),
            self.public_key)

    def test_unhexlified_key(self):
        key_bytes = binascii.unhexlify(self.public_key.get_key())
        self.assertEqual(
            PublicKey.from_hex_key(key_bytes),
            self.public_key)

    def test_bad_key(self):
        self.assertRaises(KeyParseError, PublicKey.from_hex_key, 'badkey')

    def test_bad_network_key(self):
        key = self.public_key.get_key()
        # Change the network constant
        key = "00" + key[2:]
        self.assertRaises(KeyParseError,
                          PublicKey.from_hex_key, key)


class TestVectors(TestCase):
    """Test vectors
    from https://github.com/bitcoin/bitcoin/blob/master/src/test/key_tests.cpp
    """
    def _test(self, secret, address, compressed):
        key = PrivateKey.from_wif(secret)
        self.assertEqual(key.compressed, compressed)
        self.assertEqual(address, key.get_public_key().to_address())

    def test_1(self):
        secret = "5HxWvvfubhXpYYpS3tJkw6fq9jE9j18THftkZjHHfmFiWtmAbrj"
        address = "1QFqqMUD55ZV3PJEJZtaKCsQmjLT6JkjvJ"
        self._test(secret, address, False)

    def test_2(self):
        secret = "5KC4ejrDjv152FGwP386VD1i2NYc5KkfSMyv1nGy1VGDxGHqVY3"
        address = "1F5y5E5FMc5YzdJtB9hLaUe43GDxEKXENJ"
        self._test(secret, address, False)

    def test_3(self):
        secret = "Kwr371tjA9u2rFSMZjTNun2PXXP3WPZu2afRHTcta6KxEUdm1vEw"
        address = "1NoJrossxPBKfCHuJXT4HadJrXRE9Fxiqs"
        self._test(secret, address, True)

    def test_4(self):
        secret = "L3Hq7a8FEQwJkW1M2GNKDW28546Vp5miewcCzSqUD9kCAXrJdS3g"
        address = "1CRj2HyM1CXWzHAXLQtiGLyggNT9WQqsDs"
        self._test(secret, address, True)
